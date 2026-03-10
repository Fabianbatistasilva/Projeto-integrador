from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from nutri.tests.factories import make_dieta_for_user, make_goal_and_activity, make_user


class TemplateAssetIsolationTests(TestCase):
    def setUp(self):
        self.user, self.password = make_user("template_user")
        self.objetivo, self.atividade = make_goal_and_activity()

    def _login(self):
        self.client.login(username=self.user.username, password=self.password)

    def test_home_does_not_load_create_diet_assets(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/home.css")
        self.assertNotContains(response, "css/criar_dieta.css")
        self.assertNotContains(response, "js/criar_dieta.js")

    def test_login_does_not_load_create_diet_assets(self):
        response = self.client.get(reverse("login_site"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "css/login.css")
        self.assertNotContains(response, "css/criar_dieta.css")
        self.assertNotContains(response, "js/criar_dieta.js")

    @patch("nutri.views.fetch_taco_alimentos", return_value=[])
    def test_create_diet_renders_toggle_and_expected_assets(self, _mock_fetch):
        self._login()
        make_dieta_for_user(self.user, objetivo=self.objetivo, atividade=self.atividade)

        response = self.client.get(reverse("criar_dieta"))
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, "css/criar_dieta.css")
        self.assertContains(response, "js/criar_dieta.js")
        self.assertNotContains(response, "js/tmb.js")

        self.assertContains(response, 'id="summary_toggle_btn"')
        self.assertContains(response, 'aria-expanded="true"')
        self.assertContains(response, 'aria-controls="summary_panel"')
        self.assertContains(response, 'id="summary_panel"')
