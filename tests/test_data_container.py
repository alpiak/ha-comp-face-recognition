"Tests for data container module"
import pytest

from src.data_container import DataContainer, DataContainerWithMaxSize, DictDataContainer, DictDataContainerWithMaxSize

@pytest.mark.data_container
@pytest.mark.data_container_with_max_size
@pytest.mark.dict_data_container
@pytest.mark.dict_data_container_with_max_size
@pytest.fixture
def max_waiting_num():
    return 2

@pytest.mark.data_container_with_max_size
@pytest.mark.dict_data_container_with_max_size
@pytest.fixture
def max_size():
    return 999999

@pytest.mark.data_container
@pytest.fixture
def data_container(max_waiting_num):
    return DataContainer(max_waiting_num)

@pytest.mark.data_container_with_max_size
@pytest.fixture
def data_container_with_max_size(max_waiting_num, max_size):
    return DataContainerWithMaxSize(max_size, max_waiting_num)

@pytest.mark.dict_data_container
@pytest.fixture
def dict_data_container(max_waiting_num):
    return DictDataContainer(max_waiting_num)

@pytest.mark.dict_data_container_with_max_size
@pytest.fixture
def dict_data_container_with_max_size(max_waiting_num, max_size):
    return DictDataContainerWithMaxSize(max_size, max_waiting_num)

@pytest.mark.dict_data_container
@pytest.fixture
def data_entry():
    class DataEntry(DataContainerWithMaxSize.Entry):
        def destroy(self):
            pass

    return DataEntry()

@pytest.mark.dict_data_container
@pytest.fixture
def length():
    return 3

@pytest.mark.dict_data_container
@pytest.fixture
def index():
    return 2

@pytest.mark.data_container
@pytest.mark.data_container_with_max_size
@pytest.mark.dict_data_container
@pytest.mark.dict_data_container_with_max_size
def test_init(data_container, data_container_with_max_size, dict_data_container, dict_data_container_with_max_size, max_waiting_num, max_size):
    """After instantiating, the properties should be assigned correctly."""

    assert data_container._max_waiting_num == max_waiting_num
    assert data_container._key != None
    assert data_container._locked == False

    assert data_container_with_max_size._max_size == max_size
    assert data_container_with_max_size._max_waiting_num == max_waiting_num
    assert data_container_with_max_size._key != None
    assert data_container_with_max_size._locked == False

    assert dict_data_container._max_waiting_num == max_waiting_num
    assert dict_data_container._key != None
    assert dict_data_container._locked == False

    assert dict_data_container_with_max_size._max_size == max_size
    assert dict_data_container_with_max_size._max_waiting_num == max_waiting_num
    assert dict_data_container_with_max_size._key != None
    assert dict_data_container_with_max_size._locked == False

@pytest.mark.data_container
@pytest.mark.data_container_with_max_size
@pytest.mark.dict_data_container
@pytest.mark.dict_data_container_with_max_size  
def test_init_without_optional_param():
    """When instantiating without max size, there should be no error."""

    try:
        DataContainer()
        DataContainerWithMaxSize()
        DictDataContainer()
        DictDataContainerWithMaxSize()

        assert True
    except:
        assert False

@pytest.mark.dict_data_container
def test_dict_data_container_add_and_get_all(dict_data_container, data_entry):
    """When adding new entry to the instance after locking, the entry should be added successfully."""

    dict_data_container.add(data_entry)

    assert len(dict_data_container.get_all()) == 1
    assert dict_data_container.get_all()[0] == data_entry

@pytest.mark.dict_data_container
def test_dict_data_container_update_and_get_all(dict_data_container, length, index, data_entry):
    """When updating an entry, the entry should be udpated successfully."""
    id = None

    for i in range(length):
        if i == index:
            id = dict_data_container.add(DataContainerWithMaxSize.Entry())
        else:
            dict_data_container.add(DataContainerWithMaxSize.Entry())

    assert len(dict_data_container.get_all()) == length
    assert dict_data_container.get_all()[index] != data_entry

    dict_data_container.update(id, data_entry)

    assert len(dict_data_container.get_all()) == length
    assert dict_data_container.get_all()[index] == data_entry

@pytest.mark.dict_data_container_with_max_size
def test_dict_data_container_with_max_size_no_max_size():
    """When initiate the instatance with max size as None, the max size should be None."""

    dict_data_container_with_max_size = DictDataContainerWithMaxSize(None)

    assert dict_data_container_with_max_size._max_size == None


@pytest.mark.dict_data_container_with_max_size
def test_dict_data_container_with_max_size_remove(dict_data_container_with_max_size, data_entry):
    """When remove an entry, the updated at time stamp should also be removed."""

    id = dict_data_container_with_max_size.add(data_entry)

    assert id in map(lambda entry: entry.entry_id, dict_data_container_with_max_size.get_all())

    dict_data_container_with_max_size.remove(id)

    assert id not in map(lambda entry: entry.entry_id, dict_data_container_with_max_size.get_all())

@pytest.mark.asyncio
@pytest.mark.dict_data_container_with_max_size
async def test_dict_data_container_with_max_size_any_entry_type(dict_data_container_with_max_size):
    """When adding entry of any type, no exception should be raised."""

    try:
        dict_data_container_with_max_size.add(object())

        assert True
    except TypeError:
        assert False

    try:
        dict_data_container_with_max_size.add('test')

        assert True
    except TypeError:
        assert False

    try:
        dict_data_container_with_max_size.add(DataContainer.Entry())

        assert True
    except TypeError:
        assert False
