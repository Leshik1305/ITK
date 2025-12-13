import json
from typing import Dict, Optional

import redis


class RedisQueue:
    def __init__(
        self,
        name: str = "redis_queue",
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
    ):
        self.name = name
        self.redis_client = redis.Redis(
            host=host, port=port, db=db, decode_responses=True
        )

    def publish(self, msg: Dict[str, any]) -> bool:
        try:
            data = json.dumps(msg)
            result = self.redis_client.rpush(self.name, data)
            return result > 0
        except Exception as e:
            print(f"Ошибка публикации: {e}")
            return False

    def consume(self) -> Optional[Dict]:
        try:
            result = self.redis_client.lpop(self.name)
            if result is None:
                return None

            data = json.loads(result)
            return data
        except Exception as e:
            print(f"Ошибка потребления: {e}")
            return None


if __name__ == "__main__":
    q = RedisQueue()
    q.publish({"a": 1})
    q.publish({"b": 2})
    q.publish({"c": 3})

    assert q.consume() == {"a": 1}
    assert q.consume() == {"b": 2}
    assert q.consume() == {"c": 3}
