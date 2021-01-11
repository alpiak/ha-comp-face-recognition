"""Basic class for lockable objects."""
import asyncio
from collections import deque

class Lockable:
    """Basic class for lockable objects."""

    _wrong_key_error = RuntimeError("Wrong key to update data persistence instance.")

    def __init__(self, max_waiting_num = 8):
        self._max_waiting_num = max_waiting_num
        self._key = object()
        self._locked = False
        self._lock_futures = deque()

    @property
    def locked(self):
        """Where the instance is locked for sorting."""
        return  self._locked

    async def lock(self):
        """Lock sorting and get the key."""

        if not self._locked:
            self._locked = True

            return self._key

        if (self._max_waiting_num > 0) & (len(self._lock_futures) == self._max_waiting_num):
            self.unlock(self._key)
            self._change_key()

        future = asyncio.Future()
        self._lock_futures.append(future)

        await future

        return self._key

    def unlock(self, key):
        """Unlock sorting with the key."""

        if not self._locked:
            raise RuntimeError("Data persistence instance already unlocked.")

        if key != self._key:
            raise self._wrong_key_error

        if len(self._lock_futures) > 0:
            self._lock_futures.popleft().set_result(True)

            return

        self._locked = False

    def _change_key(self):
        self._key = object()

    def _check_lock(self, key = None):
        if  self._locked:
            if key is None:
                raise RuntimeError('Can not update a data persistence instance being locked, '
                    'check if it has been lock before the operation.')

            if key != self._key:
                raise self._wrong_key_error
