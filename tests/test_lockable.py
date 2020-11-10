"Tests for lockable module"
import asyncio

import pytest

from src.lockable import Lockable

@pytest.fixture
def loop(request):
    loop = asyncio.new_event_loop()

    def fin():
        loop.close()

    request.addfinalizer(fin)

    return loop

@pytest.fixture
def max_waiting_num():
    return 2

@pytest.fixture
def lockable(max_waiting_num):
    return Lockable(max_waiting_num)

def test_init(lockable, max_waiting_num):
    """After instantiating, the properties should be assigned correctly."""

    assert lockable._max_waiting_num == max_waiting_num
    assert lockable._key != None
    assert lockable._locked == False

def test_init_without_optional_param():
    """When instantiating without max waiting time, there should be no error."""

    try:
        Lockable()

        assert True
    except:
        assert False

@pytest.mark.asyncio
async def test_lock(lockable):
    """When lock for the first time, the instance should be marked as locked immediately."""

    key = await lockable.lock()

    assert lockable._locked == True
    assert key == lockable._key

@pytest.mark.asyncio
async def test_unlock(lockable):
    """When unlock with the right key for the first time, the instance should be marked as unlocked immediately."""
    key = await lockable.lock()
    
    lockable.unlock(key)

    assert lockable._locked == False

def test_unlock_twice(loop, lockable):
    """When unlock twice, the instance should not be marked as unlocked until the second time unlock."""

    first_time_locked = None
    second_time_locked = None

    async def lock_first_time():
        key = await lockable.lock()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        lockable.unlock(key)

        nonlocal first_time_locked
        
        first_time_locked = lockable._locked

    async def lock_second_time():
        await asyncio.sleep(0)
        key = await lockable.lock()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        lockable.unlock(key)

        nonlocal second_time_locked
        
        second_time_locked = lockable._locked

    tasks = [
        lock_first_time(),
        lock_second_time()
    ]

    loop.run_until_complete(asyncio.wait(tasks))

    assert first_time_locked == True
    assert second_time_locked == False

def test_lock_twice(loop, lockable):
    """When lock twice, the second time lock should be held until the first time unlock happen."""

    first_time_unlocked = False
    first_time_unlocked_before_second_time_lock = None
    first_time_unlocked_after_second_time_lock = None

    async def lock_first_time():
        key = await lockable.lock()
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        nonlocal first_time_unlocked

        first_time_unlocked = True
        lockable.unlock(key)

    async def lock_second_time():
        await asyncio.sleep(0)

        nonlocal first_time_unlocked
        nonlocal first_time_unlocked_before_second_time_lock
        
        first_time_unlocked_before_second_time_lock = first_time_unlocked

        key = await lockable.lock()

        nonlocal first_time_unlocked_after_second_time_lock

        first_time_unlocked_after_second_time_lock = first_time_unlocked
        
        lockable.unlock(key)

    tasks= [
        lock_first_time(),
        lock_second_time()
    ]

    loop.run_until_complete((asyncio.wait(tasks)))

    assert first_time_unlocked_before_second_time_lock == False
    assert first_time_unlocked_after_second_time_lock == True

def test_change_key(loop, lockable, max_waiting_num):
    """When trying to lock over the max waiting number, the previous key can not be used anymore."""

    keys=[]
    first_unlock_err = None

    async def first_lock_and_then_unlock():
        key = await lockable.lock()

        nonlocal keys

        keys.append(key)
        
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        await asyncio.sleep(0)

        try:
            lockable.unlock(key)
        except Exception as err:
            nonlocal first_unlock_err
            
            first_unlock_err = err

    tasks=[first_lock_and_then_unlock()]

    async def lock_and_then_unlock():
        await asyncio.sleep(0)
        key = await lockable.lock()

        nonlocal keys

        keys.append(key)
        lockable.unlock(key)

    for i in range(max_waiting_num):
        tasks.append(lock_and_then_unlock())

    async def last_lock_and_then_unlock():
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        key = await lockable.lock()

        nonlocal keys

        keys.append(key)
        lockable.unlock(key)

    tasks.append(last_lock_and_then_unlock())
    loop.run_until_complete(asyncio.wait(tasks))

    assert keys[1] == keys[len(keys) - 1]
    assert keys[0] != keys[1]
    assert first_unlock_err == lockable._wrong_key_error

@pytest.mark.asyncio
async def test_check_lock(lockable):
    """When check lock with the right key during the instance being locked, no exception should be raised."""

    key = await lockable.lock()

    try:
        lockable._check_lock(key)
        
        assert True
    except:
        assert False

@pytest.mark.asyncio
async def test_check_lock_with_wrong_key(lockable):
    """When check lock without key during the instance being locked, exception should be raised."""

    await lockable.lock()

    try:
        lockable._check_lock(object())
        
        assert False
    except Exception as err:
        assert err == lockable._wrong_key_error

@pytest.mark.asyncio
async def test_check_lock_without_key(lockable):
    """When check lock without key during the instance being locked, exception should be raised."""

    await lockable.lock()

    try:
        lockable._check_lock()
        
        assert False
    except Exception as err:
        assert err.args[0] == "Can not update a data persistence instance being locked, check if it has been lock before the operation."
