"Test for storage module"
from io import BytesIO
from pathlib import Path
import asyncio
from shutil import rmtree

import pytest

from src.storage import FSStorage

@pytest.fixture
@pytest.mark.fs_storage
def asset_path():
    return "assets/yalefaces"

@pytest.fixture
@pytest.mark.fs_storage
def path():
    return "test_path"

@pytest.fixture
@pytest.mark.fs_storage
def file_name():
    return "subject01"

@pytest.fixture
@pytest.mark.fs_storage
def asset_file_name():
    return "subject01.centerlight"

@pytest.fixture
@pytest.mark.fs_storage
def asset_file_name_1():
    return "subject02.centerlight"

@pytest.fixture
@pytest.mark.fs_storage(scope="module")
def image(asset_path, asset_file_name):
    image_path = Path(asset_path) / asset_file_name
    image = None

    with image_path.open('rb') as f:
        image = f.read()

    assert image is not None
    assert len(image) > 0

    return image

@pytest.fixture
@pytest.mark.fs_storage(scope="module")
def image_1(asset_path, asset_file_name_1):
    image_path = Path(asset_path) / asset_file_name_1
    image = None

    with image_path.open('rb') as f:
        image = f.read()

    assert image is not None
    assert len(image) > 0

    return image

@pytest.mark.fs_storage
@pytest.fixture
def fs_storage():
    fs_storage = FSStorage()
    rmtree(fs_storage._base_data_path, ignore_errors = True)

    return fs_storage

@pytest.mark.asyncio
@pytest.mark.fs_storage
async def test_fs_storage(fs_storage, path, file_name, image):
    """When reading file from the storage, the file should be the same to the origin one."""
    await fs_storage.put(path, file_name, BytesIO(image))

    async with fs_storage.get(path, file_name) as f:
        f.seek(0)

        assert (await f.read()) == image

@pytest.mark.asyncio
@pytest.mark.fs_storage
async def test_fs_storage_force_put_await(fs_storage, path, file_name, image, image_1):
    """When reading file from the storage, the file should be the same to the origin one."""

    await fs_storage.put(path, file_name, BytesIO(image))

    async with fs_storage.get(path, file_name) as file:
        file.seek(0)

        assert (await file.read()) == image

    await fs_storage.put(path, file_name, BytesIO(image_1), True)

    async with fs_storage.get(path, file_name) as file:
        file.seek(0)

        file_content = await file.read()

        assert file_content != image
        assert file_content == image_1

@pytest.mark.asyncio
@pytest.mark.fs_storage
async def test_fs_storage_force_put_no_await(fs_storage, path, file_name, image, image_1):
    """When reading file from the storage, the file should be the same to the origin one."""

    asyncio.create_task(fs_storage.put(path, file_name, BytesIO(image)))
    await asyncio.sleep(0)

    async with fs_storage.get(path, file_name) as file:
        file.seek(0)

        assert (await file.read()) == image

        await fs_storage.put(path, file_name, BytesIO(image_1), True)
        await asyncio.sleep(0)

    async with fs_storage.get(path, file_name) as file:
        file.seek(0)

        file_content = await file.read()

        assert file_content != image
        assert file_content == image_1

@pytest.mark.asyncio
@pytest.mark.fs_storage
async def test_fs_storage_delete(fs_storage, path, file_name, asset_file_name):
    """When deleting a file from the storage, the file should be deleted."""
    
    image_path = Path("./assets/yalefaces/" + asset_file_name)
    image = None

    with image_path.open('rb') as f:
        image = f.read()

    assert len(image) > 0

    await fs_storage.put(path, file_name, BytesIO(image))

    async with fs_storage.get(path, file_name) as file:
        await file.seek(0)

        assert (await file.read()) == image
        assert await fs_storage.delete(path, file_name) == True

    try:
        file = fs_storage.get(path, file_name)

        assert False
    except RuntimeError as err:
        assert err.args[0] == "File not existing."

@pytest.mark.asyncio
@pytest.mark.fs_storage
async def test_fs_storage_delete_not_existing(fs_storage, path, file_name):
    """When deleting a file not existing from the storage, the operation should be indicated as failed."""
    assert await fs_storage.delete(path, file_name) == False
