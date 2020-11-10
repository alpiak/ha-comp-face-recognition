"""Components for data persistence."""
import threading
from pathlib import Path
import json

from singleton_decorator import singleton

from src.data_container import DataContainerWithMaxSize, DictDataContainerWithMaxSize

@singleton
class LocalJSONFileDictDataPersistence(DictDataContainerWithMaxSize):
    """Data persistence by storing data as a dict in local JSON file."""

    def __init__(self, max_size = 8, max_waiting_num = 8, path = '.cache', file_name = 'data.json'):
        """Initialize data persistence instance."""
        super().__init__(max_size, max_waiting_num)

        self._data_path = path
        self._file_name = file_name

        json_data = None

        try:
            with (Path(self._data_path) / self._file_name).open() as file:
                json_data = json.load(file)

                for entry_id, json_object in json_data.items():
                    if json_object["_type"] == "person":
                        # pylint: disable = cyclic-import
                        # pylint: disable = import-outside-toplevel
                        from src.person import Person
                        self._data[entry_id] = Person.from_json(json_object)
        except (PermissionError, FileNotFoundError, json.decoder.JSONDecodeError):
            pass

    def add(self, entry, key = None):
        """Add data entry."""

        if not isinstance(entry, DataContainerWithMaxSize.Entry):
            raise TypeError("Entry must be of type DataContainerWithMaxSize.Entry.")

        entry_id = super().add(entry, key)

        self._export_to_json_file()

        return entry_id

    def update(self, entry_id, entry, key = None):
        super().update(entry_id, entry, key)

        self._export_to_json_file()

    def remove(self, entry_id, key = None):
        """Remove entries by id."""
        super().remove(entry_id, key)

        self._export_to_json_file()

    def flush(self):
        """Save data in memory."""
        self._export_to_json_file()

    def _export_to_json_file(self):
        def save_file():
            path = Path(self._data_path)

            if not path.exists():
                try:
                    path.mkdir()
                except FileExistsError:
                    pass

            json_data = {}

            for entry_id, entry in self._data.items():
                json_data[entry_id] = entry.to_json()

            with (path / self._file_name).open('w') as file:
                json.dump(json_data, file)

        threading.Thread(target = save_file).start()
