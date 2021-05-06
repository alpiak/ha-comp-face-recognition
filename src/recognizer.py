"""Components for recognition."""
from typing import List
from io import BufferedIOBase, BytesIO
import asyncio

import numpy as np
import aiofiles
from aiofiles.threadpool.binary import AsyncBufferedIOBase
import cv2
import dlib
import face_recognition
from PIL import UnidentifiedImageError

from src.data_container import DictDataContainerWithMaxSize
from src.person import Person

from src.utils import wrap_obj

# pylint: disable = no-member
detector = dlib.get_frontal_face_detector()

class Recognizer:
    """Basic class for recognizers."""

    class Result:
        """The recognition result."""

        class Finding:
            """Person or other object found."""

            @property
            def target(self):
                """The recognized person."""
                return self._target

            @property
            def unkown(self):
                """Whether the target person is unkown or not."""
                return self._unkown

            def __init__(self, target: Person, unkown: bool):
                self._target = target
                self._unkown = unkown

        @property
        def findings(self):
            """Persons or objects found."""
            return self._findings

        @property
        def source(self):
            """The source image used for recognition."""
            return self._source

        def __init__(self, findings: List[Finding], source: BufferedIOBase or AsyncBufferedIOBase):
            self._findings = findings
            self._source = source

    _event_bus = None

    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def set_event_bus(self, event_bus):
        self._event_bus = event_bus
    
    def __init__(self, tolerance = .6, gpu = False):
        self._tolerance = tolerance
        self._gpu_enabled = gpu
        self._data_persistence = None
        self._storage = None
        self._event_bus = None

    def set_data_persistence(self, data_persistence):
        """Inject data persistence instance."""
        self._data_persistence = data_persistence

    def set_storage(self, storage):
        """Inject storage instance."""
        self._storage = storage

    async def recognize(self, image_file: BufferedIOBase or AsyncBufferedIOBase) -> Result:
        """Find how many faces in the image and who they are."""
        raise NotImplementedError()

class DlibRecognizer(Recognizer):
    """Dlib recognizer."""
    _storage_path = "dlib"

    def __init__(self, tolerance = .6):
        super().__init__(tolerance)

        self._face_encoding_cache = DictDataContainerWithMaxSize()

    # pylint: disable = too-many-locals
    async def recognize(self, image_file: BufferedIOBase or AsyncBufferedIOBase) -> Recognizer.Result:
        """Find faces in the image using dlib."""

        if isinstance(image_file, AsyncBufferedIOBase):
            image_file = wrap_obj(image_file, True)

        image_file.seek(0)
        image_np = face_recognition.load_image_file(image_file)

        corrupted = []
        findings = []
        matched_or_unkown_person = None

        class FaceEncoding(DictDataContainerWithMaxSize.Entry):
            """Wrap for face encoding value."""

            @property
            def value(self):
                """Face encoding value."""

                return self._value

            def __init__(self, value):
                super().__init__()

                self._value = value

            def destroy(self):
                pass

        for unknown_face_encoding, (top, right, bottom, left) in zip(
            await self._get_face_encodings(image_np),
            self._get_face_locations(image_np),
        ):
            matched_or_unkown_person = None
            unkown = False
            similarity = 0
            
            for person in filter(lambda e: isinstance(e, Person), self._data_persistence.get_all()):
                known_face_image = person.face.image
                known_face_encoding = None

                if self._face_encoding_cache.has(person.entry_id):
                    known_face_encoding = self._face_encoding_cache.get(person.entry_id).value
                else:
                    known_face_encodings = await self._get_face_encodings(known_face_image)

                    if len(known_face_encodings) == 0:
                        corrupted.append(person)

                        continue

                    known_face_encoding = known_face_encodings[0]

                    self._face_encoding_cache.add(FaceEncoding(known_face_encoding))

                score = np.sqrt(np.sum((known_face_encoding - unknown_face_encoding)**2))

                if score < self._tolerance:
                    similarity = 1 - score
                    matched_or_unkown_person = person
                    known_face_image.add_similarity(Person.Face.Image.Similarity(similarity))

            if matched_or_unkown_person is None:
                unkown = True
                matched_or_unkown_person = Person()

            # TODO: move this part to event bus

            # def on_destroy():
            #     nonlocal matched_or_unkown_person

            #     for image in matched_or_unkown_person.face.images:
            #         asyncio.create_task(self._storage.delete(self._storage_path, image.file_name))

            # matched_or_unkown_person.on("destroy", on_destroy)

            def on_destroy(person):
                if self._event_bus != None:
                    self._event_bus.trigger('destroy_person', person)

            matched_or_unkown_person.on("destroy", on_destroy)
                    
            self._data_persistence.add_or_update(matched_or_unkown_person)

            # pylint: disable = no-member
            face_image_bytes = cv2.imencode(".jpg", image_np[top: bottom, left: right])[1].tobytes()
            image_name = matched_or_unkown_person.entry_id + "_" + str(hash(face_image_bytes))

            awaitable = self._storage.put(self._storage_path, image_name, BytesIO(face_image_bytes), True)
            asyncio.create_task(awaitable)

            image = Person.Face.Image(image_name)
            image.add_similarity(Person.Face.Image.Similarity(similarity))
            matched_or_unkown_person.face.add_image(image)
            self._data_persistence.flush()
            findings.append(Recognizer.Result.Finding(matched_or_unkown_person, unkown))

        if len(corrupted) != 0:
            for person in corrupted:
                self._data_persistence.remove(person.entry_id)

        return Recognizer.Result(findings, image_file)

    async def _get_face_encodings(self, face_image):
        if face_image is None:
            return []

        def _get_face_encodings(image_np):
            if self._gpu_enabled:
                return face_recognition.face_encodings(image_np, model = "cnn")

            return face_recognition.face_encodings(image_np)

        if isinstance(face_image, Person.Face.Image):
            face_image_file = None

            try:
                async with self._storage.get(self._storage_path, face_image.file_name) as face_image_file:
                    if isinstance(face_image_file, AsyncBufferedIOBase):
                        face_image_file = wrap_obj(face_image_file, True)

                    face_image_file.seek(0)

                    try:
                        face_image_np = face_recognition.load_image_file(face_image_file)

                        return _get_face_encodings(face_image_np)
                    except (RuntimeError, UnidentifiedImageError, ValueError):
                        return []
            except RuntimeError:
                return []

        if isinstance(face_image, np.ndarray):
            return _get_face_encodings(face_image)

        raise TypeError

    def _get_face_locations(self, face_image):
        if face_image is None:
            return None

        def _get_face_locations(image_np):
            if self._gpu_enabled:
                return face_recognition.face_locations(image_np, model = "cnn")

            return face_recognition.face_locations(image_np)

        if isinstance(face_image, np.ndarray):
            return _get_face_locations(face_image)

        raise TypeError
