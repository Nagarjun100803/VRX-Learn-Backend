from faststream.redis.fastapi import RedisRouter

from src.settings import settings

router = RedisRouter(url=str(settings.redis.uri))
broker = router.broker


__all__ = ["broker", "router"]
