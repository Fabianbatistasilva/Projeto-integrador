import json


class PayloadValidationError(ValueError):
    def __init__(self, detail, status=400, error_type="validation_error"):
        super().__init__(detail)
        self.detail = detail
        self.status = status
        self.error_type = error_type


def parse_request_json_body(body_bytes):
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PayloadValidationError("payload_invalido", status=400) from exc

    if not isinstance(payload, dict):
        raise PayloadValidationError("payload_invalido", status=400)
    return payload


def validate_taco_create_payload(payload):
    if not isinstance(payload, dict):
        raise PayloadValidationError("payload_invalido", status=400)

    name = str(payload.get("name") or "").strip()
    if name == "":
        raise PayloadValidationError("Nome do alimento e obrigatorio.", status=400)

    parsed_macros = {}
    for field in ["kcal", "protein", "fat", "carbo"]:
        raw_value = payload.get(field)
        if raw_value in [None, ""]:
            raise PayloadValidationError(f"Campo {field} e obrigatorio.", status=400)
        try:
            parsed_value = int(raw_value)
        except (TypeError, ValueError) as exc:
            raise PayloadValidationError(f"Campo {field} precisa ser inteiro.", status=400) from exc
        if parsed_value < 0:
            raise PayloadValidationError(f"Campo {field} nao pode ser negativo.", status=400)
        parsed_macros[field] = parsed_value

    return {
        "name": name,
        "kcal": parsed_macros["kcal"],
        "protein": parsed_macros["protein"],
        "fat": parsed_macros["fat"],
        "carbo": parsed_macros["carbo"],
    }

