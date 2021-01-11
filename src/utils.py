from types import MethodType
from inspect import ismethod, isfunction, iscoroutinefunction, isgeneratorfunction
from io import BufferedReader, DEFAULT_BUFFER_SIZE
from asyncio import get_event_loop

from aiofiles.threadpool.binary import AsyncBufferedIOBase

from src.jsonable import JSONable

def isjsonable(obj: any):
    if obj is dict or obj is list or obj is str or obj is int or obj is float:
        return True

    if isinstance(obj, JSONable):
        return True

    return False

def wrap_obj(obj: any, sync=True):
    def wrap_fn(fn):
        """Wrap a sync function to an async function, or an async fucntion to a sync function."""
        
        if not ismethod(fn) and not isfunction(fn):
            raise TypeError('Parameter must be a function.')

        if iscoroutinefunction(fn) or isgeneratorfunction(fn):
            def sync_wrapper(*args, **kwargs):
                loop = get_event_loop()
                task = loop.create_task(fn(*args, **kwargs))
                loop.run_until_complete(task)
                
                return task.result()

            return sync_wrapper
        
        async def async_wrapper(*args, **kwargs):
            return fn(*args, **kwargs)
        
        return async_wrapper
        
    def get_attr_recursively(obj, attr_name):
        if hasattr(obj, '__dict__') and attr_name in obj.__dict__:
            return getattr(obj, attr_name)

        if hasattr(obj, '__wrapped__') and obj.__wrapped__ is not None:
            return get_attr_recursively(obj.__wrapped__, attr_name)

        raise AttributeError

    class WrapperBase(object):
        def __init__(self, obj):
            self.__wrapped__ = obj

        def __getattribute__(self, attr_name):
            attr = None

            try:
                attr = object.__getattribute__(self, attr_name)
            except AttributeError:
                attr = get_attr_recursively(self, attr_name)

            if (ismethod(attr) or isfunction(attr)):
                if not sync ^ (iscoroutinefunction(attr) or isgeneratorfunction(attr)):
                    return wrap_fn(attr)

            return attr

    if type(obj) is dict:
        class Wrapper(WrapperBase, dict):
            def _(self):
                pass

        return Wrapper(obj)

    try:
        class Wrapper(WrapperBase, dict, type(obj)):
            def _(self):
                pass

        return Wrapper(obj)
    
    except (TypeError, UnboundLocalError):
        try:
            class Wrapper(WrapperBase, type(obj), dict):
                def _(self):
                    pass
        
            return Wrapper(obj)
        except (TypeError, UnboundLocalError):
            class Wrapper(WrapperBase, type(obj)):
                def _(self):
                    pass
            
            return Wrapper(obj)

async def copy(from_file: BufferedReader or AsyncBufferedIOBase, to_file: BufferedReader or AsyncBufferedIOBase):

    async def _read(file: BufferedReader, size: int, position: int):
        file.seek(position)

        return (file.read(size), file.tell())

    async def _async_read(file: AsyncBufferedIOBase, size: int, position: int):
        await file.seek(position)

        return (await file.read(size), await file.tell())

    async def _write(file: BufferedReader, chunk, position: int):
        file.seek(position)
        file.write(chunk)

        return file.tell()

    async def _async_write(file: AsyncBufferedIOBase, chunk, position: int):
        await file.seek(position)
        await file.write(chunk)

        return await file.tell()

    read = None

    if isinstance(from_file, AsyncBufferedIOBase):
        read = _async_read
    else:
        read = _read

    write = None

    if isinstance(to_file, AsyncBufferedIOBase):
        write = _async_write
    else:
        write = _write

    read_position = 0
    write_position = 0

    chunk, read_position = await read(from_file, DEFAULT_BUFFER_SIZE, read_position)

    try:
        while chunk:
            write_position = await write(to_file, chunk ,write_position)
            chunk, read_position = await read(from_file, DEFAULT_BUFFER_SIZE, read_position)
    except IOError as err:
        raise err
