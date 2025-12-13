import random
import time

import redis

PERIOD = 3
MAX_REQUESTS = 5


class RateLimitExceed(Exception):
    pass


class RateLimiter:
    def __init__(
        self,
        name="rate_limiter",
        period=PERIOD,
        max_requests=MAX_REQUESTS,
        host="localhost",
        port=6379,
        db=0,
    ):
        self.client_redis = redis.Redis(host=host, port=port, db=db)
        self.name = name
        self.max_requests = max_requests
        self.period = period

    def test(self) -> bool:
        current_time = time.time()
        self.client_redis.zremrangebyscore(self.name, 0, current_time - self.period)
        requests_num = self.client_redis.zcard(self.name)

        if requests_num >= self.max_requests:
            return False

        self.client_redis.zadd(self.name, {str(current_time): current_time})

        return True


def make_api_request(rate_limiter: RateLimiter):
    if not rate_limiter.test():
        raise RateLimitExceed
    else:
        # какая-то бизнес логика
        pass


if __name__ == "__main__":
    rate_limiter = RateLimiter()

    for _ in range(50):
        time.sleep(
            random.uniform(0, 0.7)
        )  # Со случайными числами, которые были указаны у Вас не возможно было выйти за лимит, пришлось изменить

        try:
            make_api_request(rate_limiter)
        except RateLimitExceed:
            print(
                "Rate limit exceed!",
            )
        else:
            print("All good")
