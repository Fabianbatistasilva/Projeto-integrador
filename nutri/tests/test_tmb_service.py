from django.test import SimpleTestCase

from nutri.services.tmb_service import (
    TmbValidationError,
    parse_calculated_diet_values,
    validate_basic_tmb_fields,
)


class TmbServiceTests(SimpleTestCase):
    def test_validate_basic_tmb_fields_requires_integer_height_without_decimal(self):
        with self.assertRaises(TmbValidationError):
            validate_basic_tmb_fields(
                {"peso": "80", "height": "1,75", "age": "30", "opcao": "Masculino"}
            )

    def test_validate_basic_tmb_fields_returns_normalized_values(self):
        result = validate_basic_tmb_fields(
            {"peso": "80", "height": "175", "age": "30", "opcao": "Masculino"}
        )
        self.assertEqual(result["peso"], 80)
        self.assertEqual(result["altura"], 175)
        self.assertEqual(result["idade"], 30)
        self.assertEqual(result["sexo"], "Masculino")

    def test_parse_calculated_diet_values_rejects_missing_payload(self):
        with self.assertRaises(TmbValidationError):
            parse_calculated_diet_values("")

    def test_parse_calculated_diet_values_requires_minimum_expected_shape(self):
        with self.assertRaises(TmbValidationError):
            parse_calculated_diet_values("0,0,0")

