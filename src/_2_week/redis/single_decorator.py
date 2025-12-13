import datetime
import functools
import time
from uuid import uuid4

import redis

redis_client = redis.Redis(host="localhost", port=6379, db=0)


def single(max_processing_time: datetime.timedelta):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_key = f"lock:{func.__name__}"
            lock_id = str(uuid4())

            ttl_seconds = int(max_processing_time.total_seconds()) + 3

            lock = bool(redis_client.set(lock_key, lock_id, nx=True, ex=ttl_seconds))

            if not lock:
                print(f"{func.__name__} заблокирована другим процессом.")
                return None

            try:
                result = func(*args, **kwargs)
            finally:
                redis_client.delete(lock_key)

            return result

        return wrapper

    return decorator


@single(max_processing_time=datetime.timedelta(seconds=3))
def process_transaction():
    print("Начало транзакции")
    time.sleep(2)
    print("Завершение транзакции")


process_transaction()
