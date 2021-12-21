import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        mini_gif = (
            b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04'
            b'\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02'
            b'\x02\x4c\x01\x00\x3b'
        )
        uploaded = SimpleUploadedFile(
            name='mini.gif',
            content=mini_gif,
            content_type='image/gif'
        )
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='100',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=cls.group,
            image=uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.nonauth_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_forms_create_post_for_post_with_group_img(self):
        """Тестирование формы create_post - группа и картинка."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        test_data = {
            'text': 'Новый пост для теста форм',
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=test_data,
            follow=True
        )
        post = Post.objects.latest('id')
        with self.subTest(test_data=test_data):
            posts_count += 1
            self.assertRedirects(
                response,
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}
                )
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(Post.objects.count(), posts_count)
            self.assertEqual(
                post.text,
                test_data['text']
            )
            self.assertEqual(
                post.author,
                self.user
            )
            self.assertEqual(
                post.group.id,
                test_data['group']
            )
            self.assertEqual(
                post.image,
                f'posts/{test_data["image"].name}'
            )

    def test_forms_create_post_for_post_without_group(self):
        """Тестирование формы create_post - пост без группы."""
        posts_count = Post.objects.count()
        test_data = {
            'text': 'Второй пост для теста форм - без группы',
            'group': '',
            'image': '',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=test_data,
            follow=True
        )
        post = Post.objects.latest('id')
        with self.subTest(test_data=test_data):
            posts_count += 1
            self.assertRedirects(
                response,
                reverse(
                    'posts:profile',
                    kwargs={'username': self.user.username}
                )
            )
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(Post.objects.count(), posts_count)
            self.assertEqual(
                post.text,
                test_data['text']
            )
            self.assertEqual(
                post.author,
                self.user
            )
            self.assertEqual(
                post.group,
                None
            )
            self.assertEqual(
                post.image,
                ''
            )

    def test_forms_create_post_for_empty_post(self):
        """Тестирование формы create_post - пустой пост."""
        posts_count = Post.objects.count()
        test_data = {
            'text': '',
            'group': '',
            'image': '',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=test_data,
            follow=True
        )
        with self.subTest(test_data=test_data):
            self.assertEqual(response.status_code, HTTPStatus.OK)
            self.assertEqual(Post.objects.count(), posts_count)
            self.assertFormError(
                response,
                'form',
                'text',
                'Обязательное поле.'
            )

    def test_forms_edit_post(self):
        """Тестирование формы post_edit."""
        posts_count = Post.objects.count()
        new_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='new.gif',
            content=new_gif,
            content_type='image/gif'
        )
        edit_data = {
            'text': 'Отредактированный текст поста',
            'group': '',
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}),
            data=edit_data,
            follow=True
        )
        post = Post.objects.get(id=self.post.id)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertRedirects(
            response,
            reverse(
                'posts:post_detail',
                kwargs={'post_id': self.post.id}
            )
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(
            post.text,
            edit_data['text']
        )
        self.assertEqual(
            post.author,
            self.user
        )
        self.assertEqual(
            post.group,
            None
        )
        self.assertEqual(
            post.image,
            f'posts/{edit_data["image"].name}'
        )

    def test_forms_create_edit_post_nonauth_user(self):
        """Тестирование формы create + edit - неавторизованный пользователь."""
        urls = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id})
        ]
        login = reverse('users:login')
        posts_count = Post.objects.count()
        test_data = {
            'text': '',
            'group': '',
            'image': ''
        }
        for url in urls:
            response = self.nonauth_user.post(
                url,
                data=test_data,
                follow=True
            )
            with self.subTest(test_data=test_data):
                self.assertRedirects(
                    response,
                    f'{login}?next={url}'
                )
                self.assertEqual(Post.objects.count(), posts_count)


class CommentFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create(username='Test_User')
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст поста',
            group=None,
            image=None,
        )

    def setUp(self):
        self.nonauth_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comment_nonauth_user_redirects(self):
        """Проверка комментариев - редирект неавторизованного пользователя."""
        login = reverse('users:login')
        comment_reverse = reverse('posts:add_comment',
                                  kwargs={'post_id': self.post.id})
        comments_number = Comment.objects.count()
        test_data = {
            'text': 'Тест комментария',
            'post': self.post,
            'author': self.user,
        }
        response = self.nonauth_user.post(
            comment_reverse,
            data=test_data,
            follow=True,
        )
        with self.subTest(test_data=test_data):
            self.assertRedirects(
                response,
                f'{login}?next={comment_reverse}'
            )
            self.assertEqual(Comment.objects.count(), comments_number)

    def test_comment_creation_auth_user(self):
        """Проверка создания комментария авторизованным пользователем."""
        comment_reverse = reverse('posts:add_comment',
                                  kwargs={'post_id': self.post.id})
        redirect = reverse('posts:post_detail',
                           kwargs={'post_id': self.post.id})
        comments_number = Comment.objects.count()
        test_data = {
            'text': 'Тест комментария',
            'post': self.post,
            'author': self.user,
        }
        response = self.authorized_client.post(
            comment_reverse,
            data=test_data,
            follow=True,
        )
        with self.subTest(test_data=test_data):
            comments_number += 1
            self.assertRedirects(response, redirect)
            self.assertEqual(Comment.objects.count(), comments_number)
