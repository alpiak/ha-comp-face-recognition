"""Classes for file storage."""

import os
from time import time
from io import BytesIO
from pathlib import PurePath
from asyncio import iscoroutine

from singleton_decorator import singleton
from aiofiles import os as aioos
import aiofiles

class Storage:
    """Base class for file storage."""

    def put(self, path, name, force = False):
        """Put new file to the storage or update existing file."""
        raise NotImplementedError()

    def get(self, path, name):
        """Get file from the storage."""
        raise NotImplementedError()

    def delete(self, path, name):
        """Remove file from the storage."""
        raise NotImplementedError()

file_not_existing_error = RuntimeError("File not existing.")

@singleton
class FSStorage:
    """Class for local file system storage."""

    def __init__(self, path = '.cache'):
        self._base_data_path = path
        self._cache = {}
        self._awaitables = {}
        self._updated_at = time()

    async def put(self, path, name, file, force = False):
        """Put new file to the storage or update existing file."""

        updated_at = time()
        self._updated_at = updated_at

        file_content = file.read()

        if iscoroutine(file_content):
            file_content = await file_content

        key = path + "_" + name
        self._cache[key] = BytesIO(file_content)

        file_path = await self._prepare_path(path) / name

        if not force and os.path.exists(str(file_path)):
            raise RuntimeError("File already existing.")

        try:
            async with aiofiles.open(str(file_path), 'wb') as storage_file:
                awaitable = storage_file.write(file_content)
                self._awaitables[key] = awaitable

                await awaitable
        except IOError:
            pass

        if key in self._awaitables:
            del self._awaitables[key]

        if updated_at == self._updated_at:
            del self._cache[key]

    def get(self, path, name):
        """Get file from the storage."""
        file = self._cache.get(path + "_" + name, None)

        class Aiofile(aiofiles.threadpool.binary.AsyncBufferedIOBase):
            """Fake Async file."""

            def __init__(self, file_path, file = None):
                super().__init__(file, None, None)

                self._file_path = file_path
                self._file = file
                self._seek = 0

            def seek(self, position):
                """Set current position."""
                self._seek = position

                if self._file is not None:
                    self._file.seek(position)

            async def read(self):
                """Read file content."""
                if self._file:
                    file_content = self._file.read()

                    del self._file

                    if iscoroutine(file_content):
                        return await file_content

                    return file_content

                if not os.path.exists(self._file_path):
                    raise file_not_existing_error

                async with aiofiles.open(self._file_path, 'rb') as file:
                    file.seek(self._seek)

                    return await file.read()

        file_path_str = str(PurePath(self._base_data_path + "/" + path + "/" + name))

        if file is not None:
            return Aiofile(file_path_str, file)

        if not os.path.exists(file_path_str):
            raise file_not_existing_error

        return Aiofile(file_path_str, None)

    async def delete(self, path, name):
        """Remove file from the storage."""
        self._updated_at = time()

        key = path + "_" + name

        if key in self._awaitables:
            self._awaitables[key].cancel()
            del self._awaitables[key]
            del self._cache[key]


            return True

        try:
            await aioos.remove(str(PurePath(self._base_data_path + "/" + path + "/" + name)))

            return True
        except FileNotFoundError:
            return False

    async def _prepare_path(self, path):
        """Create directory if not exisits."""
        current_path = PurePath(".")

        for sub_path in [self._base_data_path] + path.split("/"):
            current_path = current_path / sub_path

            if not os.path.exists(str(current_path)):
                try:
                    await aioos.mkdir(str(current_path))
                except FileExistsError:
                    pass

        return current_path
