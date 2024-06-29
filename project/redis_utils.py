import redis
from project.config import settings
import json


redis_client = redis.StrictRedis.from_url(settings.REDIS_URL)


def get_cache(key: str):
    cached_result = redis_client.get(key)
    if cached_result:
        return json.loads(cached_result.decode('utf-8'))
    return None

def set_cache(key: str, value: dict, expiration: int = settings.CACHE_EXPIRATION_TIME):
    redis_client.setex(key, expiration, json.dumps(value))