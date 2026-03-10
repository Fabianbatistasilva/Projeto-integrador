from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings


@override_settings(
    AUTH_PASSWORD_VALIDATORS=[
        {
            "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
            "OPTIONS": {"min_length": 12},
        },
        {"NAME": "nutri.password_validators.StrongPasswordValidator"},
    ]
)
class StrongPasswordValidatorTests(SimpleTestCase):
    def test_rejects_password_without_required_complexity(self):
        with self.assertRaises(ValidationError) as error:
            validate_password("senhafraca1234")

        self.assertIn("maiuscula", " ".join(error.exception.messages).lower())

    def test_accepts_password_with_minimum_length_and_complexity(self):
        validate_password("SenhaForte#2026")
