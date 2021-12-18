from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from ..forms import User


class PostsFormsTests(TestCase):
    def setUp(self):
        self.nonauth_user = Client()

    def test_users_forms_create_user_valid_values(self):
        """Тестирование валидной формы users_CreationForm."""
        users_count = User.objects.count()
        test_data = {
            'first_name': 'Тест',
            'last_name': 'Тестович',
            'username': 'testuser',
            'email': 'test_user@mail.ru',
            'password1': '2021testpass',
            'password2': '2021testpass',
        }
        response = self.nonauth_user.post(
            reverse('users:signup'),
            data=test_data,
            follow=True
        )
        user = User.objects.latest('id')
        with self.subTest(test_data=test_data):
            users_count += 1
            self.assertRedirects(
                response,
                reverse('posts:index')
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(User.objects.count(), users_count)
            self.assertEqual(
                user.first_name,
                test_data['first_name']
            )
            self.assertEqual(
                user.last_name,
                test_data['last_name']
            )
            self.assertEqual(
                user.username,
                test_data['username']
            )
            self.assertEqual(
                user.email,
                test_data['email']
            )
