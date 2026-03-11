from django.http import JsonResponse

from nutri.services.http_json import json_error
from nutri.taco_client import create_alimento, is_taco_read_configured, search_alimentos
from nutri.validators.payload_validators import (
    PayloadValidationError,
    parse_request_json_body,
    validate_taco_create_payload,
)


def fetch_taco_alimentos(search_text=None, page=1):
    """Compatibilidade para telas renderizadas no servidor."""
    result = search_alimentos(search_text=search_text, page=page)
    if result.get("ok"):
        return result.get("data", {}).get("results", [])
    return []


def _build_taco_error_response(result):
    return json_error(
        detail=result.get("detail", "Falha na API TACO."),
        status=result.get("status", 502),
        error_type=result.get("error_type", "upstream_error"),
        upstream=result.get("upstream"),
    )


def taco_search(request):
    if request.user.is_authenticated is False:
        return json_error("authentication_required", status=401)
    if request.method != "GET":
        return json_error("method_not_allowed", status=405)

    search_term = (request.GET.get("search") or "").strip()
    page_raw = request.GET.get("page")
    try:
        page = int(page_raw)
    except (TypeError, ValueError):
        page = 1
    if page <= 0:
        page = 1

    result = search_alimentos(search_text=search_term, page=page)
    if not result.get("ok"):
        return _build_taco_error_response(result)

    return JsonResponse(
        result.get("data", {"count": 0, "next": None, "previous": None, "results": []}),
        status=200,
    )


def taco_create(request):
    if request.user.is_authenticated is False:
        return json_error("authentication_required", status=401)
    if request.method != "POST":
        return json_error("method_not_allowed", status=405)

    try:
        raw_payload = parse_request_json_body(request.body)
        upstream_payload = validate_taco_create_payload(raw_payload)
    except PayloadValidationError as error:
        return json_error(error.detail, status=error.status, error_type=error.error_type)

    result = create_alimento(upstream_payload)
    if not result.get("ok"):
        return _build_taco_error_response(result)

    return JsonResponse(
        {"detail": "created", "item": result.get("data", {})},
        status=result.get("status", 201),
    )


def is_taco_configured():
    return is_taco_read_configured()

