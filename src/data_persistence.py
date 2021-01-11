"""Components for data persistence."""
from typing import TypeVar, Generic
import threading
from pathlib import Path
import json

from src.jsonable import JSONable
from src.data_container import DataContainer, DictDataContainerWithMaxSize

T = TypeVar('T')

class DataPersistence(DataContainer, Generic[T]):
    @property
    def event_bus(self):
        return self._event_bus

    @event_bus.setter
    def set_event_bus(self, event_bus):
        self._event_bus = event_bus

    def __init__(self, max_size, max_waiting_num):
        super().__init__(max_size, max_waiting_num)

        self._event_bus = None

    def _persist(self):
        raise NotImplementedError

    def flush(self):
        """Save data in memory."""
        self._persist()

class DictDataPersistence(DataPersistence, DictDataContainerWithMaxSize):
    def add(self, entry, key = None):
        entry_id = super().add(entry, key)

        self._persist()

        return entry_id

    def update(self, entry_id, entry, key = None):
        super().update(entry_id, entry, key)

        self._persist()

    def remove(self, entry_id, key = None):
        """Remove entries by id."""
        super().remove(entry_id, key)

        self._persist()


class LocalJSONFileDictDataPersistence(DictDataPersistence):
    """Data persistence by storing data as a dict in local JSON file."""

    def __init__(self, max_size = 8, max_waiting_num = 8, path = '.cache', file_name = 'data.json'):
        super().__init__(max_size, max_waiting_num)

        self._data_path = path
        self._file_name = file_name

        json_data = None

        try:
            with (Path(self._data_path) / self._file_name).open() as file:
                json_data = json.load(file)

                for entry_id, json_item in json_data.items():
                    json_entry = json_item['value']
                    entry = None

                    if '_type' in json_entry and json_entry['_type'] == 'person':
                        # pylint: disable = cyclic-import
                        # pylint: disable = import-outside-toplevel
                        from src.person import Person
                        entry = Person.from_json(json_entry)

                        def on_destroy(person):
                            if self._event_bus != None:
                                self._event_bus.trigger('destroy_person', person)

                        entry.on("destroy", on_destroy)
                    else:
                        entry = json_entry

                    entry = self._set_up_entry(entry)
                    entry.entry_id = entry_id
                    entry.updated_at = json_item['updated_at']
                    self._data[entry_id] = entry
                    
        except (PermissionError, FileNotFoundError, json.decoder.JSONDecodeError):
            pass

    def _persist(self):
        def save_file():
            path = Path(self._data_path)

            if not path.exists():
                try:
                    path.mkdir()
                except FileExistsError:
                    pass

            json_data = {}

            for entry_id, entry in self._data.items():
                json_data_item = {}

                if isinstance(entry, JSONable) or hasattr(entry, 'to_json'):
                    json_data_item['value'] = entry.to_json()
                else:
                    json_data_item['value'] = entry

                json_data_item['updated_at'] = entry.updated_at

                json_data[entry_id] = json_data_item

            with (path / self._file_name).open('w') as file:
                json.dump(json_data, file)

        threading.Thread(target = save_file).start()
