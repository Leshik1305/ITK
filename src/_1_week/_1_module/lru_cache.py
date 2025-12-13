import unittest.mock
from collections import OrderedDict
from functools import wraps


def lru_cache(func=None, maxsize=None):
    """Декоратор lru_cache, с возможностью вызова с максимальной длиной кэша или без неё"""
    # Проверяем на возможность вызова без указания maxsize
    if func is not None and callable(func):
        return lru_wrapper(func, maxsize)

    # Если функция дошла до сюда, значит происходит вызов с использованием maxsize
    def decorator(func):
        return lru_wrapper(func, maxsize)

    return decorator


def lru_wrapper(func, maxsize):
    cache = OrderedDict()

    @wraps(func)
    def wrapper(*args, **kwargs):
        key_kwargs = tuple(sorted(kwargs.items())) if kwargs else ()
        key = args + key_kwargs
        if key in cache:
            # Если берем значения из кэша, передвигаем его к концу словаря
            value = cache.pop(key)
            cache[key] = value
            # print("From cache", cache)
            return value
        value = func(*args, **kwargs)
        cache[key] = value
        if maxsize is not None and len(cache) > maxsize:
            # Если кэш переполнен из начала словаря удаляем значение, которое использовалось раньше всего
            cache.popitem(last=False)
        # print("Not from cache", cache)
        return value

    return wrapper


@lru_cache
def sum(a: int, b: int) -> int:
    return a + b


@lru_cache
def sum_many(a: int, b: int, *, c: int, d: int) -> int:
    return a + b + c + d


@lru_cache(maxsize=3)
def multiply(a: int, b: int) -> int:
    return a * b


if __name__ == "__main__":
    assert sum(1, 2) == 3
    assert sum(1, 2) == 3
    assert sum(3, 4) == 7
    assert sum(3, 4) == 7

    assert multiply(1, 2) == 2
    assert multiply(3, 4) == 12

    assert sum_many(1, 2, c=3, d=4) == 10
    assert sum_many(1, 2, c=3, d=4) == 10

    mocked_func = unittest.mock.Mock()
    mocked_func.side_effect = [1, 2, 3, 4]

    decorated = lru_cache(maxsize=2)(mocked_func)
    assert decorated(1, 2) == 1
    assert decorated(1, 2) == 1
    assert decorated(3, 4) == 2
    assert decorated(3, 4) == 2
    assert decorated(5, 6) == 3
    assert decorated(5, 6) == 3
    assert decorated(1, 2) == 4
    assert mocked_func.call_count == 4
