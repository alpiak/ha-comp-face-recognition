"Tests for data persistence module"
from pathlib import Path
import asyncio
import json
from shutil import rmtree

import pytest
import singleton_decorator

from src.data_container import DataContainer, DataContainerWithMaxSize
from src.data_persistence import LocalJSONFileDictDataPersistence
from src.person import Person

@pytest.mark.local_json_file_dict_data_persistence
@pytest.fixture(scope="module")
def max_size():
    return 999999

@pytest.mark.local_json_file_dict_data_persistence
@pytest.fixture(scope="module")
def max_waiting_num():
    return 2

@pytest.mark.local_json_file_dict_data_persistence
@pytest.fixture
def json_data_persistence(request, max_size, max_waiting_num):
    LocalJSONFileDictDataPersistence._instance = None
    json_data_persistence = LocalJSONFileDictDataPersistence(max_size, max_waiting_num)

    def fin():
        rmtree(json_data_persistence._data_path, ignore_errors = True)
        
    request.addfinalizer(fin)

    return json_data_persistence

@pytest.mark.local_json_file_dict_data_persistence
@pytest.fixture
def data_entry_a():
    return Person()

@pytest.mark.local_json_file_dict_data_persistence
@pytest.fixture
def data_entry_b():
    return Person()

@pytest.mark.local_json_file_dict_data_persistence
def test_init(json_data_persistence, max_size, max_waiting_num):
    """After instantiating, the properties should be assigned correctly."""

    assert json_data_persistence._max_size == max_size
    assert json_data_persistence._max_waiting_num == max_waiting_num
    assert json_data_persistence._key != None
    assert json_data_persistence._locked == False

@pytest.mark.local_json_file_dict_data_persistence    
def test_init_without_optional_param():
    """When instantiating without optional parameters, there should be no error."""

    try:
        LocalJSONFileDictDataPersistence()

        assert True
    except:
        assert False

@pytest.mark.asyncio
@pytest.mark.local_json_file_dict_data_persistence
async def test_json_data_persistence(json_data_persistence, data_entry_a, data_entry_b):
    """When updating the data, the data should be written to and restored from the json file correctly."""

    id = json_data_persistence.add(data_entry_a)

    await asyncio.sleep(.1)

    new_json_data_persistence = LocalJSONFileDictDataPersistence()

    assert len(new_json_data_persistence.get_all()) == 1
    assert new_json_data_persistence.get_all()[0].entry_id == data_entry_a.entry_id

    del new_json_data_persistence

    json_data_persistence.update(id, data_entry_b)
    
    await asyncio.sleep(.1)

    new_json_data_persistence = LocalJSONFileDictDataPersistence()

    assert len(new_json_data_persistence.get_all()) == 1
    assert new_json_data_persistence.get_all()[0].entry_id == data_entry_b.entry_id

@pytest.mark.asyncio
@pytest.mark.local_json_file_dict_data_persistence
async def test_json_data_persistence_any_entry_type(json_data_persistence):
    """When adding entry of any type, no exception should be raised."""

    try:
        json_data_persistence.add(object())

        assert True
    except TypeError:
        assert False

    try:
        json_data_persistence.add('test')

        assert True
    except TypeError:
        assert False

    try:
        json_data_persistence.add(DataContainer.Entry())

        assert True
    except TypeError:
        assert False
