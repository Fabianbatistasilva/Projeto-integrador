import json
import os
import subprocess
import sys
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from nutri.models import ImprimirDieta
from nutri.tests.factories import make_dieta_for_user, make_goal_and_activity, make_user


class CreateDietViewTests(TestCase):
    def setUp(self):
        self.user, self.password = make_user("create_diet_user")
        self.objetivo, self.atividade = make_goal_and_activity()

    def _login(self):
        self.client.login(username=self.user.username, password=self.password)

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_redirects_anonymous_user_to_login(self, _mock_fetch):
        response = self.client.get(reverse("criar_dieta"))
        self.assertRedirects(response, reverse("login_site"))

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_redirects_authenticated_user_without_dieta_to_tmb(self, _mock_fetch):
        self._login()
        response = self.client.get(reverse("criar_dieta"))
        self.assertRedirects(response, reverse("tela_tmb"))

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_rejects_empty_payload(self, _mock_fetch):
        self._login()
        make_dieta_for_user(self.user, objetivo=self.objetivo, atividade=self.atividade)

        response = self.client.post(reverse("criar_dieta"), {})
        self.assertRedirects(response, reverse("criar_dieta"))
        self.assertFalse(ImprimirDieta.objects.filter(usuario=self.user).exists())

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_rejects_invalid_json_payload(self, _mock_fetch):
        self._login()
        make_dieta_for_user(self.user, objetivo=self.objetivo, atividade=self.atividade)

        response = self.client.post(reverse("criar_dieta"), {"diet_payload": "{invalido"})
        self.assertRedirects(response, reverse("criar_dieta"))
        self.assertFalse(ImprimirDieta.objects.filter(usuario=self.user).exists())

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_saves_valid_payload_and_syncs_legacy_fields(self, _mock_fetch):
        self._login()
        make_dieta_for_user(self.user, objetivo=self.objetivo, atividade=self.atividade)

        payload = {
            "selected_meals": 2,
            "meals": [
                {
                    "refeicao": 1,
                    "items": [
                        {
                            "name": "Arroz Branco cozido",
                            "quantidade": 200,
                            "kcal_base": 130,
                            "prot_base": 3,
                            "gord_base": 1,
                            "carb_base": 28,
                        }
                    ],
                },
                {
                    "refeicao": 2,
                    "items": [
                        {
                            "name": "Peito de Frango cozido",
                            "quantidade": 150,
                            "kcal_base": 165,
                            "prot_base": 31,
                            "gord_base": 4,
                            "carb_base": 0,
                        }
                    ],
                },
            ],
        }

        response = self.client.post(reverse("criar_dieta"), {"diet_payload": json.dumps(payload)})
        self.assertRedirects(response, reverse("diet_screen"))

        dieta = ImprimirDieta.objects.get(usuario=self.user)
        self.assertEqual(dieta.itens.count(), 2)

        first_item = dieta.itens.filter(refeicao=1).first()
        second_item = dieta.itens.filter(refeicao=2).first()

        self.assertEqual(first_item.alimento, "Arroz Branco cozido")
        self.assertEqual(first_item.quantidade, 200)
        self.assertEqual(first_item.kcal, 260)
        self.assertEqual(first_item.prot, 6)
        self.assertEqual(first_item.gord, 2)
        self.assertEqual(first_item.carb, 56)

        self.assertEqual(second_item.alimento, "Peito de Frango cozido")
        self.assertEqual(second_item.quantidade, 150)
        self.assertEqual(second_item.kcal, 247)
        self.assertEqual(second_item.prot, 46)
        self.assertEqual(second_item.gord, 6)
        self.assertEqual(second_item.carb, 0)

        self.assertEqual(dieta.ref_11, "Arroz Branco cozido")
        self.assertEqual(dieta.quant_11, 200)
        self.assertEqual(dieta.kcal_11, 260)
        self.assertEqual(dieta.ref_21, "Peito de Frango cozido")
        self.assertEqual(dieta.quant_21, 150)


class TacoSearchViewTests(TestCase):
    def setUp(self):
        self.user, self.password = make_user("taco_search_user")
        cache.clear()

    def _login(self):
        self.client.login(username=self.user.username, password=self.password)

    def test_requires_authentication(self):
        response = self.client.get(reverse("taco_search"))
        self.assertEqual(response.status_code, 401)

    @override_settings(TACO_API_BASE_URL="")
    def test_returns_503_when_api_is_not_configured(self):
        self._login()
        response = self.client.get(reverse("taco_search"))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "API TACO nao configurada neste ambiente.")

    @override_settings(TACO_API_BASE_URL="http://fake.taco")
    @patch("nutri.views.requests.get")
    def test_returns_upstream_results(self, mock_get):
        self._login()

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {"name": "Arroz", "kcal": 130, "protein": 3, "fat": 0, "carbo": 28}
            ]
        }
        mock_get.return_value = mock_response

        response = self.client.get(reverse("taco_search"), {"search": "arroz"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["results"]), 1)

        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "http://fake.taco/alimentos/")
        self.assertEqual(kwargs["params"]["search"], "arroz")

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_SEARCH_CACHE_SECONDS=300)
    @patch("nutri.views.requests.get")
    def test_uses_cache_for_repeated_search(self, mock_get):
        self._login()

        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {"name": "Arroz", "kcal": 130, "protein": 3, "fat": 0, "carbo": 28}
            ]
        }
        mock_get.return_value = mock_response

        first = self.client.get(reverse("taco_search"), {"search": "arroz"})
        second = self.client.get(reverse("taco_search"), {"search": "arroz"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(mock_get.call_count, 1)


class TacoCreateViewTests(TestCase):
    def setUp(self):
        self.user, self.password = make_user("taco_create_user")
        self.valid_payload = {
            "name": "Alimento Teste",
            "kcal": 100,
            "protein": 10,
            "fat": 5,
            "carbo": 12,
        }

    def _login(self):
        self.client.login(username=self.user.username, password=self.password)

    def test_requires_authentication(self):
        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)

    def test_rejects_non_post_methods(self):
        self._login()
        response = self.client.get(reverse("taco_create"))
        self.assertEqual(response.status_code, 405)

    @override_settings(TACO_API_BASE_URL="")
    def test_returns_503_when_api_not_configured(self):
        self._login()
        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="")
    def test_returns_503_when_api_token_not_configured(self):
        self._login()
        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["detail"], "Token da API TACO nao configurado neste ambiente.")

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="fake-token")
    def test_rejects_invalid_json_payload(self):
        self._login()
        response = self.client.post(
            reverse("taco_create"),
            data="{invalid",
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "payload_invalido")

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="fake-token")
    def test_rejects_payload_with_missing_field(self):
        self._login()
        payload = self.valid_payload.copy()
        payload.pop("protein")
        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("Campo protein", response.json()["detail"])

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="fake-token")
    def test_rejects_negative_macro_values(self):
        self._login()
        payload = self.valid_payload.copy()
        payload["fat"] = -1
        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("nao pode ser negativo", response.json()["detail"])

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="fake-token")
    @patch("nutri.views.requests.post")
    def test_propagates_upstream_error(self, mock_post):
        self._login()
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"detail": "erro_upstream"}
        mock_post.return_value = mock_response

        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["detail"], "erro_upstream")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Token fake-token")

    @override_settings(TACO_API_BASE_URL="http://fake.taco", TACO_API_TOKEN="fake-token")
    @patch("nutri.views.requests.post")
    def test_returns_success_when_upstream_creates_food(self, mock_post):
        self._login()
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"id": 1, "name": "Alimento Teste"}
        mock_post.return_value = mock_response

        response = self.client.post(
            reverse("taco_create"),
            data=json.dumps(self.valid_payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["detail"], "created")
        _, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Token fake-token")


class UserRegistrationViewTests(TestCase):
    def test_fails_when_passwords_do_not_match(self):
        response = self.client.post(
            reverse("registration_screen"),
            {"username": "ana", "password": "SenhaForte#2026", "conf_password": "SenhaForte#2027"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="ana").exists())

    def test_fails_when_username_already_exists(self):
        make_user("usuario_existente", "SenhaForte#2026")
        response = self.client.post(
            reverse("registration_screen"),
            {"username": "usuario_existente", "password": "SenhaForte#2026", "conf_password": "SenhaForte#2026"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username="usuario_existente").count(), 1)

    def test_fails_when_password_is_weak(self):
        response = self.client.post(
            reverse("registration_screen"),
            {"username": "senha_fraca", "password": "abc12345", "conf_password": "abc12345"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="senha_fraca").exists())
        self.assertIn("senha", response.content.decode().lower())

    def test_creates_user_and_redirects_to_login(self):
        response = self.client.post(
            reverse("registration_screen"),
            {"username": "novo_usuario", "password": "SenhaForte#2026", "conf_password": "SenhaForte#2026"},
        )
        self.assertRedirects(response, reverse("login_site"))
        self.assertTrue(User.objects.filter(username="novo_usuario").exists())


class UserLoginSecurityTests(TestCase):
    def setUp(self):
        self.user, self.password = make_user("login_security_user", "abc123")
        cache.clear()

    @override_settings(LOGIN_MAX_ATTEMPTS=2, LOGIN_BLOCK_SECONDS=300)
    def test_blocks_after_multiple_failed_attempts(self):
        login_url = reverse("login_site")

        first = self.client.post(login_url, {"username": self.user.username, "password": "errada"})
        second = self.client.post(login_url, {"username": self.user.username, "password": "errada"})
        third = self.client.post(login_url, {"username": self.user.username, "password": "errada"})

        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(third.status_code, 200)
        self.assertContains(third, "Muitas tentativas de login")


class SettingsHardeningTests(SimpleTestCase):
    def _base_production_env(self):
        env = os.environ.copy()
        env["DJANGO_DEBUG"] = "false"
        env["DJANGO_ALLOWED_HOSTS"] = "example.com"
        env["DJANGO_CSRF_TRUSTED_ORIGINS"] = "https://example.com"
        env["DJANGO_SECRET_KEY"] = "x" * 64
        env["DATABASE_URL"] = "postgres://user:pass@localhost:5432/nutrients"
        env["REDIS_URL"] = "redis://localhost:6379/0"
        env["TACO_API_BASE_URL"] = "https://api.example.com"
        return env

    def _import_settings(self, env):
        return subprocess.run(  # noqa: S603
            [sys.executable, "-c", "import conf.settings"],
            capture_output=True,
            text=True,
            env=env,
            check=False,
        )

    def test_production_without_redis_url_fails_fast(self):
        env = self._base_production_env()
        env.pop("REDIS_URL", None)

        result = self._import_settings(env)
        combined = (result.stdout or "") + (result.stderr or "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("REDIS_URL", combined)

    def test_production_without_database_url_fails_fast(self):
        env = self._base_production_env()
        env.pop("DATABASE_URL", None)

        result = self._import_settings(env)
        combined = (result.stdout or "") + (result.stderr or "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DATABASE_URL", combined)

    def test_production_without_csrf_trusted_origins_fails_fast(self):
        env = self._base_production_env()
        env.pop("DJANGO_CSRF_TRUSTED_ORIGINS", None)

        result = self._import_settings(env)
        combined = (result.stdout or "") + (result.stderr or "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_CSRF_TRUSTED_ORIGINS", combined)

    def test_production_rejects_local_taco_api_base_url(self):
        env = self._base_production_env()
        env["TACO_API_BASE_URL"] = "http://127.0.0.1:7000"

        result = self._import_settings(env)
        combined = (result.stdout or "") + (result.stderr or "")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("TACO_API_BASE_URL", combined)


class HealthcheckViewTests(TestCase):
    def test_returns_200_when_database_is_available(self):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["database"], "ok")
        self.assertEqual(payload["cache"], "ok")
        self.assertIn("timestamp", payload)

    @patch("nutri.views.connection.cursor", side_effect=Exception("db_down"))
    def test_returns_503_when_database_check_fails(self, _mock_cursor):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["database"], "error")
        self.assertEqual(payload["cache"], "ok")

    @override_settings(DEBUG=False)
    @patch("nutri.views.cache.set", side_effect=Exception("cache_down"))
    def test_returns_503_when_cache_check_fails_in_production(self, _mock_cache_set):
        response = self.client.get(reverse("healthcheck"))
        self.assertEqual(response.status_code, 503)
        payload = response.json()
        self.assertEqual(payload["status"], "degraded")
        self.assertEqual(payload["database"], "ok")
        self.assertEqual(payload["cache"], "error")
