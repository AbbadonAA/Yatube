from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

User = get_user_model()


class StaticViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='Test User')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.static_pages = {
            reverse('users:signup'): ('users/signup.html', 'all'),
            reverse('users:logout'): ('users/logged_out.html', 'all'),
            reverse('users:login'): ('users/login.html', 'all'),
            reverse('users:password_change'):
            ('users/password_change.html', 'auth'),
            reverse('users:password_change_done'):
            ('users/password_change_done.html', 'auth'),
            reverse('users:password_reset'):
            ('users/password_reset.html', 'all'),
            reverse('users:password_reset_done'):
            ('users/password_reset_done.html', 'all'),
            reverse('users:password_reset_confirm',
                    kwargs={'token': '123', 'uidb64': '222'}):
            ('users/password_reset_confirm.html', 'all'),
            reverse('users:password_reset_complete'):
            ('users/password_reset_complete.html', 'all'),
        }

    def test_users_views_accessible_and_correct_template(self):
        """Тестирование доступности страниц и корр. шаблонов users."""
        def check_200_template(response):
            with self.subTest(response=response):
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template[0])
        for name, template in self.static_pages.items():
            if template[1] == 'auth':
                response = self.authorized_client.get(name)
                check_200_template(response)
            else:
                response = self.guest_client.get(name)
                check_200_template(response)

    def test_users_views_correct_context(self):
        """Тестирование контекста users:signup."""
        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        response = self.guest_client.get(reverse('users:signup'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
