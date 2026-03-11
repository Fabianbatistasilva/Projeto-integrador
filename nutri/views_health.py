from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils import timezone


def healthcheck(request):
    db_ok = True
    cache_ok = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        db_ok = False

    try:
        cache_key = "healthcheck::cache_probe"
        probe_value = timezone.now().isoformat()
        cache.set(cache_key, probe_value, timeout=30)
        cached_value = cache.get(cache_key)
        if cached_value != probe_value:
            cache_ok = False
    except Exception:
        cache_ok = False

    status_code = 200
    if not db_ok:
        status_code = 503
    elif not cache_ok and not settings.DEBUG:
        status_code = 503

    return JsonResponse(
        {
            "status": "ok" if db_ok and cache_ok else "degraded",
            "app": "nutrients",
            "database": "ok" if db_ok else "error",
            "cache": "ok" if cache_ok else "error",
            "timestamp": timezone.now().isoformat(),
        },
        status=status_code,
    )

