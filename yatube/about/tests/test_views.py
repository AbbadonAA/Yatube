from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class StaticViewsTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.static_pages = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }

    def test_about_views_accessible_and_correct_template(self):
        """Тестирование доступности страниц и корректности шаблонов about."""
        for name, template in self.static_pages.items():
            response = self.guest_client.get(name)
            with self.subTest(response=response):
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
