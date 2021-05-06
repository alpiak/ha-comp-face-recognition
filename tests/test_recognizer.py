"Tests for recognizer module"
import os
from io import BytesIO
from pathlib import Path
from shutil import rmtree
import asyncio

import pytest
import aiofiles
import singleton_decorator

from src.data_persistence import LocalJSONFileDictDataPersistence
from src.storage import FSStorage
from src.recognizer import DlibRecognizer
from src.person import Person

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="module")
def asset_path():
    return "assets/yalefaces"

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="module")
def get_image_bytes(asset_path):
    def get_image_bytes(file_name):
        image_path = Path(asset_path) / file_name

        assert os.path.exists(str(image_path))

        with open(str(image_path), 'rb') as file:
            return file.read()

    return get_image_bytes

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="function")
def image_file_1_of_person_a(get_image_bytes):
    return BytesIO(get_image_bytes("subject01.centerlight"))

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="function")
def image_file_2_of_person_a(get_image_bytes):
    return BytesIO(get_image_bytes("subject01.normal"))

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="function")
def image_file_1_of_person_b(get_image_bytes):
    return BytesIO(get_image_bytes("subject02.centerlight"))

@pytest.mark.dlib_recognizer
@pytest.fixture
def json_data_persistence(request):
    LocalJSONFileDictDataPersistence._instance = None
    json_data_persistence = LocalJSONFileDictDataPersistence()

    def fin():
        singleton_decorator.decorator._SingletonWrapper._instance = None

        try:
            (Path(json_data_persistence._data_path) / json_data_persistence._file_name).unlink()
            Path(json_data_persistence._data_path).rmdir()
        except (FileNotFoundError, OSError):
            pass

    request.addfinalizer(fin)

    return json_data_persistence

@pytest.mark.dlib_recognizer
@pytest.fixture(scope="module")
def fs_storage(request):
    fs_storage = FSStorage()

    def fin():
        try:
            rmtree(fs_storage._base_data_path, True)
        except FileNotFoundError:
            pass

    request.addfinalizer(fin)

    return fs_storage

@pytest.mark.dlib_recognizer
@pytest.fixture
def dlib_regconizer(json_data_persistence, fs_storage):
    regconizer = DlibRecognizer()
    regconizer.set_data_persistence(json_data_persistence)
    regconizer.set_storage(fs_storage)

    return regconizer

@pytest.mark.dlib_recognizer
@pytest.mark.asyncio
async def test_dlib_regconizer_first_time(dlib_regconizer, image_file_1_of_person_a, fs_storage):
    """When processing the image of one person for the first time, the person should be regconized."""

    result = await dlib_regconizer.recognize(image_file_1_of_person_a)

    assert len(result.findings) == 1

    await asyncio.sleep(0)

    async with fs_storage.get(dlib_regconizer._storage_path, result.findings[0].target.face.image.file_name) as file:
        image = await file.read()

        assert image is not None
        assert len(image) > 0

@pytest.mark.dlib_recognizer
@pytest.mark.asyncio
async def test_dlib_regconizer_one_person_two_time(dlib_regconizer, image_file_1_of_person_a, json_data_persistence, fs_storage):
    """When processing one same image of one person for two times, one same person should be regconized."""

    await dlib_regconizer.recognize(image_file_1_of_person_a)
    result = await dlib_regconizer.recognize(image_file_1_of_person_a)

    assert len(result.findings) == 1
    assert len(list(filter(lambda entry: isinstance(entry, Person), json_data_persistence.get_all()))) == 1

    await asyncio.sleep(0)
    async with fs_storage.get(dlib_regconizer._storage_path, result.findings[0].target.face.image.file_name) as f:
        f.seek(0)

        image = await f.read()

        assert image is not None
        assert len(image) > 0

@pytest.mark.dlib_recognizer
@pytest.mark.asyncio
async def test_dlib_regconizer_one_person_two_images(dlib_regconizer, image_file_1_of_person_a, image_file_2_of_person_a, json_data_persistence, fs_storage):
    """When processing two images of one person, one same person should be regconized."""

    await dlib_regconizer.recognize(image_file_1_of_person_a)
    await asyncio.sleep(0)
    result = await dlib_regconizer.recognize(image_file_2_of_person_a)

    assert len(result.findings) == 1
    assert len(list(filter(lambda entry: isinstance(entry, Person), json_data_persistence.get_all()))) == 1
    assert len(result.findings[0].target.face.images) == 2

    face_image = result.findings[0].target.face.images[0]
    face_image_1 = result.findings[0].target.face.images[1]

    assert face_image.similarity < face_image_1.similarity

    await asyncio.sleep(0)
    async with fs_storage.get(dlib_regconizer._storage_path, face_image.file_name) as file:
        await file.seek(0)

        image = await file.read()

        async with fs_storage.get(dlib_regconizer._storage_path, face_image_1.file_name) as file_1:
            file_1.seek(0)

            image_1 = await file_1.read()

            assert image is not None
            assert image_1 is not None
            assert len(image) > 0
            assert len(image_1) > 0
            assert image != image_1

@pytest.mark.dlib_recognizer
@pytest.mark.asyncio
async def test_dlib_regconizer_two_persons(dlib_regconizer, image_file_1_of_person_a, image_file_1_of_person_b, json_data_persistence, fs_storage):
    """When processing two images of two different persons, two different persons should be regconized."""

    await dlib_regconizer.recognize(image_file_1_of_person_a)
    await asyncio.sleep(0)
    await dlib_regconizer.recognize(image_file_1_of_person_b)

    saved_persons = list(filter(lambda entry: isinstance(entry, Person), json_data_persistence.get_all()))

    assert len(saved_persons) == 2
    assert len(saved_persons[0].face.images) == 1
    assert len(saved_persons[1].face.images) == 1

    face_image = saved_persons[0].face.images[0]
    face_image_1 = saved_persons[1].face.images[0]

    await asyncio.sleep(0)
    async with fs_storage.get(dlib_regconizer._storage_path, face_image.file_name) as image_file:
        await image_file.seek(0)
        image = await image_file.read()

        async with fs_storage.get(dlib_regconizer._storage_path, face_image_1.file_name) as image_file_1:
            await image_file_1.seek(0)
            image_1 = await image_file_1.read()

            assert image is not None
            assert image_1 is not None
            assert len(image) > 0
            assert len(image_1) > 0
            assert image != image_1

    