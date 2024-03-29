from http import HTTPStatus

from django.test import Client, TestCase

from ..models import Comment, Group, Post, User


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test_User')
        cls.user_author = User.objects.create_user(username='Post_Author')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='100',
            description='Описание тестовой группы',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый текст поста',
            group=cls.group,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Комментарий для теста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = Client()
        self.authorized_client.force_login(self.user)
        self.author.force_login(self.user_author)
        self.url_templates = {
            '/': ('posts/index.html', 'all'),
            '/follow/': ('posts/follow.html', 'auth'),
            f'/group/{self.group.slug}/': ('posts/group_list.html', 'all'),
            f'/profile/{self.user.username}/': ('posts/profile.html', 'all'),
            '/create/': ('posts/create_post.html', 'auth'),
            f'/posts/{self.post.id}/': ('posts/post_detail.html', 'all'),
            f'/posts/{self.post.id}/edit/': ('posts/create_post.html',
                                             'author'),
            '/unexisting_page/': (None, '404'),
        }
        self.urls_redirects = {
            f'/posts/{self.post.id}/comment/': f'/posts/{self.post.id}/',
            f'/profile/{self.user.username}/follow/':
            f'/profile/{self.user.username}/',
            f'/profile/{self.user.username}/unfollow/':
            f'/profile/{self.user.username}/',
        }

    def check_access(self, url_templates):
        """Проверка доступности страниц по статусу авторизации."""
        def check_200_and_template(response, url, template, user):
            """Проверка доступности страниц, переданных в check_access()."""
            with self.subTest(url=url):
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK,
                    f'Страница по адресу {url} недоступна для '
                    f'{user}'
                )
            with self.subTest(url=url):
                self.assertTemplateUsed(
                    response,
                    template[0],
                    f'Шаблон {template[0]} не существует или некорректен для '
                    f'адреса {url}'
                )

        def check_404(response, url, user):
            """Проверка запроса к несуществующей странице и вывода 404."""
            with self.subTest(url=url):
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.NOT_FOUND,
                    f'Запрос от {user} к несуществующей странице не ведет на '
                    f'страницу {HTTPStatus.NOT_FOUND}'
                )
        for url, template in url_templates.items():
            if template[1] == 'all':
                user = 'Неавторизованный пользователь'
                response = self.guest_client.get(url)
                check_200_and_template(response, url, template, user)
            elif template[1] == 'auth':
                user = 'Авторизованный пользователь'
                response = self.authorized_client.get(url)
                check_200_and_template(response, url, template, user)
            elif template[1] == 'author':
                user = 'Автор поста'
                response = self.author.get(url)
                check_200_and_template(response, url, template, user)
            else:
                user = 'Любой пользователь'
                response = self.guest_client.get(url)
                check_404(response, url, user)

    def test_url_redirect_anonymous_and_non_author(self):
        """Тестирование корректных редиректов пользователей posts."""
        for url, template in self.url_templates.items():
            if template[1] == 'author':
                response = self.authorized_client.get(url, follow=True)
                with self.subTest(url=url):
                    self.assertRedirects(response, f'/posts/{self.post.id}/')
            if template[1] != 'all' and template[1] != '404':
                response = self.guest_client.get(url, follow=True)
                with self.subTest(url=url):
                    self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_url_template_accessibility(self):
        """Тестирование URLS - доступность страниц posts и шаблонов."""
        self.check_access(self.url_templates)

    def test_urls_follow(self):
        for url, redirect in self.urls_redirects.items():
            response = self.authorized_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
            self.assertRedirects(response, redirect)
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.FOUND)
