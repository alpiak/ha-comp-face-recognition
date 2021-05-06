from types import MethodType, BuiltinFunctionType, BuiltinMethodType
from inspect import ismethod, isfunction, iscoroutinefunction, isgeneratorfunction
from io import BufferedReader, DEFAULT_BUFFER_SIZE
from asyncio import get_event_loop

import nest_asyncio
from aiofiles.threadpool.binary import AsyncBufferedIOBase

from src.jsonable import JSONable

def isjsonable(obj: any):
    if obj is dict or obj is list or obj is str or obj is int or obj is float:
        return True

    if isinstance(obj, JSONable):
        return True

    return False

def wrap_obj(obj: any, sync=True, base_class=None):
    """Wrap an object in order to add custom attribute to it later."""

    def wrap_fn(fn):
        """Wrap a sync function to an async function, or an async fucntion to a sync function."""
        
        if not ismethod(fn) and not isfunction(fn) and not isinstance(fn, BuiltinFunctionType) and not isinstance(fn, BuiltinMethodType):
            raise TypeError('Parameter must be a function.')

        if iscoroutinefunction(fn) or isgeneratorfunction(fn):
            def sync_wrapper(*args, **kwargs):
                loop = get_event_loop()
                nest_asyncio.apply(loop)
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

    class WrapperBase(base_class if base_class != None else object):
        def __init__(self, obj):
            self.__wrapped__ = obj

        def __getattribute__(self, attr_name):
            attr = None

            try:
                attr = object.__getattribute__(self, attr_name)
            except AttributeError:
                attr = get_attr_recursively(self, attr_name)

            if ismethod(attr) or isfunction(attr) or isinstance(attr, BuiltinFunctionType) or isinstance(attr, BuiltinMethodType):
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

DAY = 1000 * 60 * 60 * 24
HOUR = 1000 * 60 * 60
MINUTE = 1000 * 60
SECOND = 1000

def milliseconds_to_string(milliseconds, lang = 'en-US'):
    days = milliseconds // DAY
    remains = milliseconds % DAY
    hours = remains // HOUR
    remains = remains % HOUR
    minutes = remains // MINUTE
    remains = remains % MINUTE
    seconds = remains // SECOND

    if lang == 'zh-CN' or lang == 'zh':
        def get_component_zh(args):
            [value, unit] = args

            if value == 0:
                return None

            if value == 1:
                return str(value) + unit
            
            return str(value) + unit

        return ''.join(filter(lambda component: component is not None, map(get_component_zh, [
            [days, '天'],
            [hours, '小时'],
            [minutes, '分钟'],
            [seconds, '秒'],
        ]))) or '瞬时'
        
    def get_component_en(args):
        [value, unit_singular, unit_plural] = args

        if value == 0:
            return None

        if value == 1:
            return str(value) + ' ' + unit_singular
        
        return str(value) + ' ' + unit_plural

    return ' '.join(filter(lambda component: component is not None, map(get_component_en, [
        [days, 'day', 'days'],
        [hours, 'hour', 'hours'],
        [minutes, 'minute', 'minutes'],
        [seconds, 'second', 'seconds'],
    ]))) or '1 seconds'
