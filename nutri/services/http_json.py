from django.http import JsonResponse


def json_error(detail, status, error_type=None, upstream=None):
    payload = {"detail": detail}
    if error_type:
        payload["error_type"] = error_type
    if isinstance(upstream, dict) and upstream:
        payload["upstream"] = upstream
    return JsonResponse(payload, status=status)


def json_ok(payload, status=200):
    return JsonResponse(payload, status=status)

