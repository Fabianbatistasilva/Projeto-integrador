import logging
import time
from urllib.parse import urlparse

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


def _normalize_endpoint_path(raw_endpoint):
    endpoint = str(raw_endpoint or "").strip()
    if endpoint == "":
        return ""
    if "://" in endpoint:
        return ""
    if not endpoint.startswith("/"):
        return ""
    if not endpoint.endswith("/"):
        endpoint = f"{endpoint}/"
    return endpoint


def _validate_endpoint_setting(raw_endpoint, setting_name):
    endpoint = str(raw_endpoint or "").strip()
    if endpoint == "":
        return ""
    if "://" in endpoint or not endpoint.startswith("/"):
        return f"{setting_name} deve ser path relativo iniciando com '/'."
    return ""


def _validate_base_url_setting(raw_base_url):
    base_url = str(raw_base_url or "").strip().rstrip("/")
    if base_url == "":
        return "API TACO nao configurada neste ambiente."

    parsed_base = urlparse(base_url)
    host = str(parsed_base.hostname or "").lower()
    if parsed_base.scheme not in {"http", "https"} or host == "":
        return "TACO_API_BASE_URL invalida. Use URL http/https valida."
    if host in {"127.0.0.1", "localhost", "0.0.0.0"}:
        return "TACO_API_BASE_URL nao pode apontar para localhost/127.0.0.1."
    return ""


def _resolve_taco_endpoint_url(raw_base_url, raw_endpoint):
    base_url = str(raw_base_url or "").strip().rstrip("/")
    if base_url == "":
        return ""

    parsed_base = urlparse(base_url)
    if parsed_base.scheme and parsed_base.netloc:
        root = f"{parsed_base.scheme}://{parsed_base.netloc}".rstrip("/")
        legacy_path = str(parsed_base.path or "").strip("/")
    else:
        # Mantem robustez em desenvolvimento para base sem schema.
        root = base_url
        legacy_path = ""

    endpoint = _normalize_endpoint_path(raw_endpoint)
    if endpoint != "":
        return f"{root}{endpoint}"

    # Compatibilidade legada: base configurada com path (ex.: .../alimentos/).
    if legacy_path != "":
        return f"{root}/{legacy_path}/"
    return ""


def get_taco_read_url():
    return _resolve_taco_endpoint_url(
        getattr(settings, "TACO_API_BASE_URL", ""),
        getattr(settings, "TACO_API_ALIMENTOS_READ_ENDPOINT", "/alimentos/"),
    )


def get_taco_write_url():
    return _resolve_taco_endpoint_url(
        getattr(settings, "TACO_API_BASE_URL", ""),
        getattr(settings, "TACO_API_ALIMENTOS_WRITE_ENDPOINT", "/alimentos/"),
    )


def is_taco_read_configured():
    return get_taco_read_url() != ""


def get_taco_api_token():
    return str(getattr(settings, "TACO_API_TOKEN", "") or "").strip()


def is_taco_write_configured():
    return get_taco_write_url() != "" and get_taco_api_token() != ""


def _taco_auth_headers():
    token = get_taco_api_token()
    if token == "":
        return {}
    return {"Authorization": f"Token {token}"}


def extract_taco_results(payload):
    if isinstance(payload, dict):
        results = payload.get("results")
        if isinstance(results, list):
            return results
    if isinstance(payload, list):
        return payload
    return []


def _extract_detail(payload, fallback_message):
    if isinstance(payload, dict):
        detail = payload.get("detail")
        if isinstance(detail, str) and detail.strip() != "":
            return detail.strip()
    return fallback_message


def _normalize_search_payload(payload):
    if isinstance(payload, dict):
        results = extract_taco_results(payload)
        return {
            "count": payload.get("count", len(results)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": results,
        }
    results = extract_taco_results(payload)
    return {"count": len(results), "next": None, "previous": None, "results": results}


def _search_cache_key(search_text, page):
    search = str(search_text or "").strip().lower()
    return f"taco_alimentos::search={search}::page={int(page)}"


def search_alimentos(search_text=None, page=1):
    base_url_error = _validate_base_url_setting(
        getattr(settings, "TACO_API_BASE_URL", ""),
    )
    if base_url_error:
        return {
            "ok": False,
            "status": 503,
            "detail": base_url_error,
            "error_type": "config_error",
            "upstream": {},
        }

    endpoint_error = _validate_endpoint_setting(
        getattr(settings, "TACO_API_ALIMENTOS_READ_ENDPOINT", "/alimentos/"),
        "TACO_API_ALIMENTOS_READ_ENDPOINT",
    )
    if endpoint_error:
        return {
            "ok": False,
            "status": 503,
            "detail": endpoint_error,
            "error_type": "config_error",
            "upstream": {},
        }

    api_url = get_taco_read_url()
    if api_url == "":
        return {
            "ok": False,
            "status": 503,
            "detail": "API TACO nao configurada neste ambiente.",
            "error_type": "config_error",
            "upstream": {},
        }

    page_int = 1
    try:
        page_int = int(page)
    except (TypeError, ValueError):
        page_int = 1
    if page_int <= 0:
        page_int = 1

    cache_key = _search_cache_key(search_text, page_int)
    cached_payload = cache.get(cache_key)
    if cached_payload is not None:
        return {"ok": True, "status": 200, "data": cached_payload}

    params = {"ordering": "name", "page": page_int}
    normalized_search = str(search_text or "").strip()
    if normalized_search != "":
        params["search"] = normalized_search

    start_time = time.monotonic()
    try:
        response = requests.get(
            api_url,
            params=params,
            timeout=getattr(settings, "TACO_API_TIMEOUT", 8),
        )
    except requests.Timeout:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning(
            "taco_request_failed method=GET reason=timeout endpoint=alimentos_read elapsed_ms=%s",
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": 504,
            "detail": "Tempo limite ao consultar API TACO.",
            "error_type": "timeout",
            "upstream": {},
        }
    except requests.RequestException:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning(
            "taco_request_failed method=GET reason=connection_error endpoint=alimentos_read elapsed_ms=%s",
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": 502,
            "detail": "Falha ao conectar na API TACO.",
            "error_type": "connection_error",
            "upstream": {},
        }

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    try:
        payload = response.json()
    except ValueError:
        payload = {}

    if response.status_code >= 400:
        status_code = response.status_code if response.status_code < 500 else 502
        detail = _extract_detail(payload, "Falha ao buscar alimentos na API TACO.")
        logger.warning(
            "taco_request_failed method=GET reason=upstream_error endpoint=alimentos_read status=%s elapsed_ms=%s",
            response.status_code,
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": status_code,
            "detail": detail,
            "error_type": "upstream_error",
            "upstream": payload if isinstance(payload, dict) else {},
        }

    normalized_payload = _normalize_search_payload(payload)
    cache.set(
        cache_key,
        normalized_payload,
        timeout=getattr(settings, "TACO_SEARCH_CACHE_SECONDS", 60),
    )
    logger.info(
        "taco_request_ok method=GET endpoint=alimentos_read status=%s elapsed_ms=%s count=%s",
        response.status_code,
        elapsed_ms,
        normalized_payload.get("count", 0),
    )
    return {"ok": True, "status": 200, "data": normalized_payload}


def create_alimento(payload):
    base_url_error = _validate_base_url_setting(
        getattr(settings, "TACO_API_BASE_URL", ""),
    )
    if base_url_error:
        return {
            "ok": False,
            "status": 503,
            "detail": base_url_error,
            "error_type": "config_error",
            "upstream": {},
        }

    endpoint_error = _validate_endpoint_setting(
        getattr(settings, "TACO_API_ALIMENTOS_WRITE_ENDPOINT", "/alimentos/"),
        "TACO_API_ALIMENTOS_WRITE_ENDPOINT",
    )
    if endpoint_error:
        return {
            "ok": False,
            "status": 503,
            "detail": endpoint_error,
            "error_type": "config_error",
            "upstream": {},
        }

    api_url = get_taco_write_url()
    if api_url == "":
        return {
            "ok": False,
            "status": 503,
            "detail": "API TACO nao configurada neste ambiente.",
            "error_type": "config_error",
            "upstream": {},
        }

    headers = _taco_auth_headers()
    if "Authorization" not in headers:
        return {
            "ok": False,
            "status": 503,
            "detail": "Token da API TACO nao configurado neste ambiente.",
            "error_type": "missing_token",
            "upstream": {},
        }

    start_time = time.monotonic()
    try:
        response = requests.post(
            api_url,
            json=payload,
            headers=headers,
            timeout=getattr(settings, "TACO_API_WRITE_TIMEOUT", 10),
        )
    except requests.Timeout:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning(
            "taco_request_failed method=POST reason=timeout endpoint=alimentos_write elapsed_ms=%s",
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": 504,
            "detail": "Tempo limite ao criar alimento na API TACO.",
            "error_type": "timeout",
            "upstream": {},
        }
    except requests.RequestException:
        elapsed_ms = int((time.monotonic() - start_time) * 1000)
        logger.warning(
            "taco_request_failed method=POST reason=connection_error endpoint=alimentos_write elapsed_ms=%s",
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": 502,
            "detail": "Falha ao conectar na API TACO.",
            "error_type": "connection_error",
            "upstream": {},
        }

    elapsed_ms = int((time.monotonic() - start_time) * 1000)
    try:
        response_payload = response.json()
    except ValueError:
        response_payload = {}

    if response.status_code >= 400:
        status_code = response.status_code if response.status_code < 500 else 502
        detail = _extract_detail(response_payload, "Falha ao criar alimento na API TACO.")
        logger.warning(
            "taco_request_failed method=POST reason=upstream_error endpoint=alimentos_write status=%s elapsed_ms=%s",
            response.status_code,
            elapsed_ms,
        )
        return {
            "ok": False,
            "status": status_code,
            "detail": detail,
            "error_type": "upstream_error",
            "upstream": response_payload if isinstance(response_payload, dict) else {},
        }

    logger.info(
        "taco_request_ok method=POST endpoint=alimentos_write status=%s elapsed_ms=%s",
        response.status_code,
        elapsed_ms,
    )
    return {
        "ok": True,
        "status": 201 if response.status_code == 201 else 200,
        "data": response_payload if isinstance(response_payload, dict) else {},
    }
