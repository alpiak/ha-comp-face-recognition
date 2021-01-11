"""Classes for data container."""
from typing import TypeVar, Generic, List
from types import MethodType
from time import time
from uuid import uuid4

from src.lockable import Lockable

from src.utils import isjsonable, wrap_obj

T = TypeVar('T')

class DataContainer(Lockable, Generic[T]):
    """Base class for data container."""

    # pylint: disable = too-few-public-methods
    class Entry:
        """Entry type for the data container."""

        def __init__(self):
            self.entry_id = None

        def destroy(self):
            """Clean up the entry data."""
            raise NotImplementedError()

    @staticmethod
    def _set_up_entry(entry: T):
        if hasattr(entry, 'entry_id') and hasattr(entry, 'destroy') and isjsonable(entry):
            return entry

        def set_attr(entry):
            if not hasattr(entry, 'entry_id'):
                setattr(entry, 'entry_id', None)

            if not hasattr(entry, 'destroy'):
                setattr(entry, 'destroy', MethodType(lambda self: None, entry))

        try:
            set_attr(entry)
        except AttributeError:
            entry = wrap_obj(entry)
            set_attr(entry)

        return entry

    def add(self, entry: T, key = None) -> str:
        self._check_lock(key)

    def update(self, entry_id, entry: T, key = None):
        """Update a data entry."""
        raise NotImplementedError()

    def add_or_update(self, entry: T, key = None):
        """Update a data entry or add it if not existing."""

        if not hasattr(entry, 'entry_id') or not entry.entry_id:
            self.add(entry, key)

        try:
            self.add(entry, key)
        except RuntimeError:
            self.update(entry.entry_id, entry, key)

    def has(self, entry_id, key = None) -> bool:
        """Check if the entry id exists."""
        raise NotImplementedError()

    def get(self, entry_id, key = None) -> any:
        """Get entry by id"""
        raise NotImplementedError()

    def remove(self, entry_id, key = None):
        """Remove entry by id."""
        raise NotImplementedError()

    def get_all(self) -> List[T]:
        """Get all data entry."""
        raise NotImplementedError()

class DataContainerWithMaxSize(DataContainer, Generic[T]):
    """Base class for data containers with max size."""

    class Entry(DataContainer.Entry):
        """Entry type for the data container with max size."""

        def __init__(self):
            super().__init__()

            self.updated_at = None

        def refresh(self):
            """Set new update time."""
            self.updated_at = time()

        def destroy(self):
            """Clean up the entry data."""
            raise NotImplementedError()

    def __init__(self, max_size: int or None = 8, max_waiting_num: int = 8):
        super().__init__(max_waiting_num)

        self._max_size: int or None = max_size

    def add(self, entry, key = None):
        super().add(entry, key)

        entry = self._set_up_entry(entry)

        self._check_id(entry)
        entry.refresh()
        self._check_max_size()

        return entry.entry_id

    def get_all(self):
        """Get all data entry."""
        raise NotImplementedError()

    def get_all_sorted(self) -> List[T]:
        """Get all data entry sorted."""
        return sorted(self.get_all(), key = self._get_sort_key)

    def _check_id(self, entry: Entry):
        """Add id to the entry if not exists."""
        raise NotImplementedError()

    def _generate_id(self, entry: Entry):
        """Generate entry id."""
        raise NotImplementedError()

    def _get_sort_key(self, entry):
        """Get the key to sort entry."""
        raise NotImplementedError()

    def _check_max_size(self):
        """Remove item when exceed the max size."""

        if self._max_size is None:
            return

        entries = self.get_all()

        if len(entries) > self._max_size:
            self.remove(self.get_all_sorted()[0].entry_id)

    def _set_up_entry(self, entry):
        entry = super()._set_up_entry(entry)

        if hasattr(entry, 'updated_at') and hasattr(entry, 'refresh') and isjsonable(entry):
            return entry

        def set_attr(entry):
            if not hasattr(entry, 'updated_at'):
                setattr(entry, 'updated_at', time())
            
            if not hasattr(entry, 'refresh'):
                setattr(entry, 'refresh', MethodType(getattr(DataContainerWithMaxSize.Entry, 'refresh'), entry))

        try:
            set_attr(entry)

            if not isjsonable(entry):
                entry = wrap_obj(entry)
        except AttributeError:
            entry = wrap_obj(entry)
            set_attr(entry)

        return entry

class DictDataContainer(DataContainer):
    """Data container that have the data as a dict in the memory."""

    def __init__(self, max_waiting_num = 8):
        super().__init__(max_waiting_num)

        self._data = {}

    def add(self, entry, key = None):
        super().add(entry, key)

        entry = self._set_up_entry(entry)

        if entry.entry_id and entry.entry_id in self._data:
            raise RuntimeError("Id already existing.")

        self._check_id(entry)
        self._data[entry.entry_id] = entry

        return entry.entry_id

    def update(self, entry_id, entry, key = None):
        self._check_lock(key)

        entry = self._set_up_entry(entry)
        entry.entry_id = entry_id

        if not entry_id in self._data:
            raise RuntimeError("Id not existing.")

        self._data[entry_id] = entry

    def has(self, entry_id, key=None):
        self._check_lock(key)

        if entry_id in self._data:
            return True

        return False

    def get(self, entry_id, key = None):
        self._check_lock(key)

        if not entry_id in self._data:
            raise RuntimeError("Id not existing.")

        return self._data[entry_id]

    def remove(self, entry_id, key = None):
        self._check_lock(key)
        self._data[entry_id].destroy()

        del self._data[entry_id]

    def get_all(self):
        return list(self._data.values())

    def _check_id(self, entry):
        """Add id to the entry if not exists."""

        if not entry.entry_id:
            entry.entry_id = self._generate_id(entry)

    def _generate_id(self, entry):
        """Generate entry id."""
        entry_id = entry.entry_id

        if entry_id and entry_id not in self._data:
            return entry_id

        if entry_id in self._data and entry == self._data[entry_id]:
            return entry_id

        while True:
            entry_id = str(uuid4())
            duplicated = False

            for exsisting_entry in self.get_all():
                if exsisting_entry.entry_id == entry_id:
                    duplicated = True

            if not duplicated:
                return entry_id

class DictDataContainerWithMaxSize(DictDataContainer, DataContainerWithMaxSize):
    """Data container that have the data as a dict in the memory."""

    def __init__(self, max_size: int or None = 8, max_waiting_num = 8):
        """Initialize data container instance."""

        DictDataContainer.__init__(self, max_waiting_num)
        DataContainerWithMaxSize.__init__(self, max_size, max_waiting_num)

    def add(self, entry, key = None):
        """Add data entry."""

        entry_id = DictDataContainer.add(self, entry, key)
        entry_id = DataContainerWithMaxSize.add(self, entry, key)

        return entry_id

    def _get_sort_key(self, entry):
        """Get the key to sort entry."""
        return entry.updated_at
