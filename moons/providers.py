try:
    from django_redis import get_redis_connection
    _client = get_redis_connection("default")
except (NotImplementedError, ModuleNotFoundError):
    from django.core.cache import caches
    default_cache = caches['default']
    _client = default_cache.get_master_client()

cache_client = _client
