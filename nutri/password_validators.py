import re

from django.core.exceptions import ValidationError


class StrongPasswordValidator:
    def validate(self, password, user=None):
        raw_password = str(password or "")
        errors = []

        if re.search(r"[A-Z]", raw_password) is None:
            errors.append("Senha deve conter pelo menos 1 letra maiuscula.")
        if re.search(r"[a-z]", raw_password) is None:
            errors.append("Senha deve conter pelo menos 1 letra minuscula.")
        if re.search(r"\d", raw_password) is None:
            errors.append("Senha deve conter pelo menos 1 numero.")
        if re.search(r"[^A-Za-z0-9]", raw_password) is None:
            errors.append("Senha deve conter pelo menos 1 simbolo.")

        if errors:
            raise ValidationError(errors)

    def get_help_text(self):
        return (
            "Sua senha deve ter no minimo 12 caracteres e conter maiuscula, "
            "minuscula, numero e simbolo."
        )
