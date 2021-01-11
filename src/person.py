"""Class for persons."""
from observable import Observable

from src.jsonable import JSONable
from src.data_persistence import LocalJSONFileDictDataPersistence
from src.data_container import DataContainerWithMaxSize, DictDataContainerWithMaxSize

class Person(JSONable, LocalJSONFileDictDataPersistence.Entry, Observable):
    """Class for persons."""

    class Face(JSONable):
        """Face of the person."""

        class ImageContainer(DictDataContainerWithMaxSize):
            """Container for images."""

            def add(self, entry, key = None):
                if not isinstance(entry, Person.Face.Image):
                    raise TypeError("Entry must be of type Image.")

                super().add(entry, key)

            def _get_sort_key(self, entry):
                """Get the sort key for sortting entry."""
                return entry.similarity

        class Image(JSONable, DataContainerWithMaxSize.Entry):
            """Class for images."""

            class Similarity(JSONable, DataContainerWithMaxSize.Entry):
                """Class for similarity values."""

                @property
                def value(self):
                    """Similarity value."""
                    return self._value

                def __init__(self, value):
                    JSONable.__init__(self, "similarity")
                    DataContainerWithMaxSize.Entry.__init__(self)

                    self._value = value

                def destroy(self):
                    pass

                @classmethod
                def from_json(cls, json_object):
                    """Create the entry from json object."""

                    similarity = cls(json_object["_value"])
                    similarity.entry_id = json_object["entry_id"]
                    similarity.updated_at = json_object["updated_at"]

                    return similarity

                def to_json(self):
                    """Convert the entry to json object."""

                    return {
                        "entry_id": self.entry_id,
                        "_value": self._value,
                        "updated_at": self.updated_at
                    }

            class Similarities(DictDataContainerWithMaxSize):
                """Container for similarity values."""

                def add(self, entry, key = None):
                    if not isinstance(entry, Person.Face.Image.Similarity):
                        raise TypeError("Entry must be of type Similarity.")

                    super().add(entry, key)

                def get_average(self):
                    """Get average similarity."""
                    if len(self.get_all()) == 0:
                        if self._get_summary() > 0:
                            raise RuntimeError

                        return 0

                    return self._get_summary() / len(self.get_all())

                def _get_summary(self):
                    """Get the summary of all similarity values."""
                    summary = 0

                    for similarity in self.get_all():
                        summary = summary + similarity.value

                    return summary

                def _get_sort_key(self, entry):
                    """Get the key to sort entry."""
                    return entry.value

            @property
            def file_name(self):
                """File name of the image."""
                return self._file_name

            @property
            def similarity(self):
                """Similarity of the image in total."""
                return self._similarities.get_average()

            def __init__(self, file_name):
                super().__init__("image")

                self._file_name = file_name
                self._similarities = Person.Face.Image.Similarities()

            def add_similarity(self, similarity):
                """Add similarity value to the image."""
                self._similarities.add(similarity)

            def destroy(self):
                pass

            @classmethod
            def from_json(cls, json_object):
                """Create the entry from json object."""
                image = cls(json_object["file_name"])
                image.entry_id = json_object["entry_id"]

                for similarity in json_object["_similarities"]:
                    image.add_similarity(cls.Similarity.from_json(similarity))

                image.updated_at = json_object["updated_at"]

                return image

            def to_json(self):
                """Convert the entry to json object."""

                return {
                    "entry_id": self.entry_id,
                    "file_name": self.file_name,
                    "_similarities": list(map(lambda s: s.to_json(), self._similarities.get_all())),
                    "updated_at": self.updated_at
                }

        @property
        def image(self):
            """Get the face image of the person with the best quality."""
            images = self.images

            if len(images) == 0:
                return None

            return images[len(images) - 1]

        @property
        def images(self):
            """Get asll the face images of the person."""
            return self._images.get_all_sorted()

        def __init__(self):
            super().__init__('face')

            self._images = Person.Face.ImageContainer()

        def add_image(self, image):
            """Add face image."""
            return self._images.add(image)

        @classmethod
        def from_json(cls, json_object):
            face = Person.Face()

            for image in json_object["images"]:
                face.add_image(cls.Image.from_json(image))

            return face

        def to_json(self):
            """Convert the entry to json object."""
            return { "images": list(map(lambda image: image.to_json(), self.images)) }

    @property
    def face(self):
        """Face of the person."""
        return self._face

    def __init__(self, name = None, face = None):
        JSONable.__init__(self, 'person')
        LocalJSONFileDictDataPersistence.Entry.__init__(self)
        Observable.__init__(self)

        self._name = name

        if face is not None:
            self._face = face
        else:
            self._face = Person.Face()

    def destroy(self):
        self.trigger("destroy", self)

    @classmethod
    def from_json(cls, json_object):
        """Create the entry from json object."""

        person = cls(json_object["_name"], cls.Face.from_json(json_object["face"]))
        person.entry_id = json_object["entry_id"]

        person.updated_at = json_object["updated_at"]

        return person

    def to_json(self):
        """Convert the entry to json object."""

        return {
            "_type": self._type,
            "entry_id": self.entry_id,
            "_name": self._name,
            "face": self.face.to_json(),
            "updated_at": self.updated_at
        }
