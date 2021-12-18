from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Test User')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.url_templates = {
            '/auth/logout/': ('users/logged_out.html', 'all'),
            '/auth/signup/': ('users/signup.html', 'all'),
            '/auth/login/': ('users/login.html', 'all'),
            '/auth/password_change/': ('users/password_change.html', 'auth'),
            '/auth/password_change/done/':
            ('users/password_change_done.html', 'auth'),
            '/auth/password_reset/': ('users/password_reset.html', 'all'),
            '/auth/password_reset/done/':
            ('users/password_reset_done.html', 'all'),
            '/auth/reset/<uidb64>/<token>/':
            ('users/password_reset_confirm.html', 'all'),
            '/auth/reset/done/': ('users/password_reset_complete.html', 'all'),
        }

    def check_200_and_template(self, response, url, template):
        """Проверка доступности страниц, переданных в test_users_urls...()."""
        with self.subTest(url=url):
            self.assertEqual(
                response.status_code,
                HTTPStatus.OK,
                f'Страница по адресу {url} недоступна для '
            )
        with self.subTest(url=url):
            self.assertTemplateUsed(
                response,
                template[0],
                f'Шаблон {template[0]} не существует или некорректен для '
                f'адреса {url}'
            )

    def test_users_url_uses_correct_template(self):
        """Проверка доступности страниц и корректности шаблонов users."""
        for url, template in self.url_templates.items():
            if template[1] == 'auth':
                response = self.authorized_client.get(url)
                self.check_200_and_template(response, url, template)
            else:
                response = self.guest_client.get(url)
                self.check_200_and_template(response, url, template)
