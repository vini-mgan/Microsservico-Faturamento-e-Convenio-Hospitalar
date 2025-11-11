import redis
from redis.exceptions import ConnectionError, RedisError
from app.config import settings
import logging

logger = logging.getLogger(__name__)

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
    decode_responses=True,
    socket_connect_timeout=2,
    socket_timeout=2
)


def get_redis():
    """Retorna cliente Redis com tratamento de erros"""
    try:
        # Testa conexão
        redis_client.ping()
        return redis_client
    except (ConnectionError, RedisError) as e:
        logger.warning(f"Redis não disponível: {e}")
        return None
