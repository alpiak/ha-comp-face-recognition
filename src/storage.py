"""Classes for file storage."""

import os
from time import time
from io import BufferedIOBase
from pathlib import PurePath
from asyncio import iscoroutine

from singleton_decorator import singleton
from aiofiles import os as aioos
from aiofiles.threadpool.binary import AsyncBufferedIOBase
import aiofiles

from src.utils import wrap_obj, copy

class Storage:
    """Base class for file storage."""

    async def put(self, path, name, file: BufferedIOBase or AsyncBufferedIOBase, force = False):
        """Put new file to the storage or update existing file."""
        raise NotImplementedError()

    def get(self, path, name, sync = False):
        """Get file from the storage."""
        raise NotImplementedError()

    async def delete(self, path, name):
        """Remove file from the storage."""
        raise NotImplementedError()

file_not_existing_error = RuntimeError("File not existing.")

@singleton
class FSStorage:
    """Class for local file system storage."""

    def __init__(self, path = '.cache'):
        self._base_data_path = path
        self._cache = {}
        self._updated_at = {}

    async def put(self, path, name, file, force = False):
        """Put new file to the storage or update existing file."""

        key = path + "_" + name
        updated_at = time()
        self._updated_at[key] = updated_at

        file_path = await self._prepare_path(path) / name

        self._cache[key] = file

        if not force and os.path.exists(str(file_path)):
            raise RuntimeError("File already existing.")

        try:
            async with aiofiles.open(str(file_path), 'wb') as storage_file:
                await copy(file, storage_file)
        except IOError:
            pass

        if key in self._updated_at and updated_at == self._updated_at[key]:
            del self._cache[key]
            del self._updated_at[key]

    def get(self, path, name, sync = False):
        """Get file from the storage."""
        file = self._cache.get(path + "_" + name, None)

        file_path_str = str(PurePath(self._base_data_path + "/" + path + "/" + name))

        if file is not None:
            if sync ^ isinstance(file, BufferedIOBase):
                return wrap_obj(file, sync)
                
            return file

        if not os.path.exists(file_path_str):
            raise file_not_existing_error

        if sync:
            return open(file_path_str, 'rb')

        return aiofiles.open(file_path_str, 'rb')

    async def delete(self, path, name):
        """Remove file from the storage."""
        key = path + "_" + name

        if key in self._updated_at:
            del self._updated_at[key]

        if key in self._cache:
            del self._cache[key]

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
