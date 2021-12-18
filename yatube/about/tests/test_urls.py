from http import HTTPStatus

from django.test import Client, TestCase


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.static_pages = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }

    def test_about_url_uses_correct_template(self):
        """Проверка доступности страниц и корректности шаблонов."""
        for url, template in self.static_pages.items():
            response = self.guest_client.get(url)
            with self.subTest(url=url):
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница по адресу {url} недоступна.'
                )
                self.assertTemplateUsed(
                    response,
                    template,
                    f'Шаблон {template} некорректен.'
                )
