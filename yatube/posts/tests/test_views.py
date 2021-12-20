from django import forms
from django.core.cache import cache
from django.core.cache.backends import locmem
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import P_PER_L

from ..models import Comment, Group, Post, User


class PostsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User')
        cls.user_author = User.objects.create_user(username='Post Author')
        cls.group = Group.objects.create(
            title='Заголовок тестовой группы',
            slug='100',
            description='Описание тестовой группы',
        )
        cls.group_empty = Group.objects.create(
            title='Вторая группа',
            slug='200',
            description='Группа без поста',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый текст поста',
            group=cls.group,
        )
        comment_example = [
            Comment(
                author=cls.user,
                text=f'Комментарий для тестов номер {number}',
                post=cls.post
            )
            for number in range(1, 5)
        ]
        cls.comments = Comment.objects.bulk_create(comment_example)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.author = Client()
        self.authorized_client.force_login(self.user)
        self.author.force_login(self.user_author)
        self.names_templates = {
            reverse('posts:index'): ('posts/index.html', 'all', 'show_cont'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                   ('posts/group_list.html', 'all', 'show_cont'),
            reverse('posts:profile',
                    kwargs={'username': self.user_author.username}):
                   ('posts/profile.html', 'all', 'show_cont'),
            reverse('posts:post_create'):
                   ('posts/create_post.html', 'auth', 'None'),
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}):
                   ('posts/post_detail.html', 'all', 'None'),
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}):
                   ('posts/create_post.html', 'author', 'None'),
        }

    def tearDown(self):
        cache.clear()

    def test_views_uses_correct_templates(self):
        """Тестирование корректности используемых в Views шаблонов."""
        for reverse_name, template in self.names_templates.items():
            if template[1] == 'author':
                with self.subTest(reverse_name=reverse_name):
                    response = self.author.get(reverse_name)
                    self.assertTemplateUsed(response, template[0])
            else:
                with self.subTest(reverse_name=reverse_name):
                    response = self.authorized_client.get(reverse_name)
                    self.assertTemplateUsed(response, template[0])

    def test_views_create_edit_post_use_correct_context(self):
        """Тестирование контекста у шаблонов create_post и edit."""
        def check_context(response):
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
                'image': forms.fields.ImageField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(form_field, expected)

        for reverse_name, template in self.names_templates.items():
            if template[1] == 'auth':
                response = self.authorized_client.get(reverse_name)
                check_context(response)
            elif template[1] == 'author':
                response = self.author.get(reverse_name)
                check_context(response)
                self.assertEqual(response.context.get('is_edit'), True)

    def correct_context_for_post_page_obj(self, response):
        """Проверка правильности контекста страниц со списком постов."""
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)

    def test_index_show_correct_context(self):
        """Тестирование правильности контекста шаблона index."""
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context_for_post_page_obj(response)

    def test_group_posts_show_correct_context(self):
        """Тестирование правильности контекста шаблона group_posts."""
        response = (self.authorized_client.
                    get(reverse('posts:group_list',
                                kwargs={'slug': self.group.slug})))
        self.correct_context_for_post_page_obj(response)
        self.assertEqual(response.context.get('group'), self.post.group)

    def test_profile_show_correct_context(self):
        """Тестирование правильности контекста шаблона profile."""
        response = (self.authorized_client.
                    get(reverse('posts:profile',
                                kwargs={
                                    'username': self.user_author.username
                                })))
        self.correct_context_for_post_page_obj(response)
        self.assertEqual(response.context.get('author'), self.post.author)
        self.assertEqual(response.context.get('counter'),
                         self.post.author.post.count())

    def test_post_detail_show_correct_context(self):
        """Тестирование правильности контекста шаблона post_detail."""
        response = (self.authorized_client.
                    get(reverse('posts:post_detail',
                                kwargs={'post_id': self.post.id})))
        post = response.context.get('post')
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.image, self.post.image)
        self.assertEqual(response.context.get('counter'),
                         self.post.author.post.count())
        self.assertEqual(post.comments.count(), Comment.objects.count())
        self.assertEqual(post.comments.latest('id').text,
                         Comment.objects.latest('id').text)

    def test_post_in_correct_group(self):
        """Тестирование отображения поста и отсутствия в случайной группе."""
        for reverse_name, template in self.names_templates.items():
            response = self.authorized_client.get(reverse_name)
            if template[2] == 'show_cont':
                post = response.context['page_obj'][0]
                with self.subTest(reverse_name=reverse_name):
                    self.assertEqual(post.text, self.post.text)
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.group_empty.slug})
        )
        self.assertNotIn(self.post, response.context['page_obj'])

    def test_views_index_cache_page_20_seconds(self):
        """Проверка кеширования списка постов страницы index."""
        self.assertEqual(not locmem._caches[''], True)
        response = self.authorized_client.get(reverse('posts:index'))
        self.correct_context_for_post_page_obj(response)
        response_second = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(response_second.context, None)
        self.assertEqual(not locmem._caches[''], False)


class PaginatorViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Test User Pagin')
        cls.group = Group.objects.create(
            title='Группа для теста пагинатора',
            slug='group_pagin',
            description='Описание группы'
        )
        cls.post_example = [
            Post(
                author=cls.user,
                text=f'Теcтовый пост номер {number}',
                group=cls.group
            )
            for number in range(1, 16)
        ]
        cls.post = Post.objects.bulk_create(cls.post_example)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.names_templates = {
            reverse('posts:index'): ('posts/index.html', 'all', 'show_cont'),
            reverse('posts:group_list', kwargs={'slug': self.group.slug}):
                   ('posts/group_list.html', 'all', 'show_cont'),
            reverse('posts:profile',
                    kwargs={'username': self.user.username}):
                   ('posts/profile.html', 'all', 'show_cont'),
        }

    def test_paginator_pages_and_posts_count(self):
        """Тестирование корректной работы паджинатора."""
        post_count = Post.objects.count()
        page_count = 1
        while post_count > P_PER_L:
            post_count -= P_PER_L
            page_count += 1

        def check_paginator(response):
            with self.subTest(reverse_name=reverse_name):
                self.assertEqual(len(
                    response.context.get('page_obj').object_list),
                    post_count
                )
                self.assertEqual(
                    response.context.get('page_obj').paginator.num_pages,
                    page_count
                )
        for reverse_name in self.names_templates.keys():
            if Post.objects.count() >= 10:
                response = self.client.get(
                    reverse_name + f'?page={page_count}'
                )
                check_paginator(response)
                self.assertEqual(len(
                    response.context.get(
                        'page_obj'
                    ).paginator.page(1).object_list),
                    P_PER_L
                )
            else:
                response = self.client.get(reverse_name)
                check_paginator(response)


class SubscriptionsViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = User.objects.create_user(username='First_User')
        cls.user2 = User.objects.create_user(username='Second_User')
        cls.user3 = User.objects.create_user(username='Third_User')
        cls.post = Post.objects.create(
            author=cls.user1,
            text='Тестовый текст поста',
            group=None,
        )
        cls.post2 = Post.objects.create(
            author=cls.user2,
            text='Второй пост',
            group=None,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client1 = Client()
        self.authorized_client2 = Client()
        self.authorized_client3 = Client()
        self.authorized_client1.force_login(self.user1)
        self.authorized_client2.force_login(self.user2)
        self.authorized_client3.force_login(self.user3)
        self.url_follow1 = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user1.username}
        )
        self.url_follow2 = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user2.username}
        )
        self.url_follow3 = reverse(
            'posts:profile_follow',
            kwargs={'username': self.user3.username}
        )
        self.url_unfollow1 = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user1.username}
        )
        self.url_unfollow2 = reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.user2.username}
        )

    def tearDown(self):
        cache.clear()

    def check_subscriptions(
        self, response, user1_followers, user1_followings,
        user2_followers, user2_followings, user3_followers,
        user3_followings, author
    ):
        with self.subTest(response=response):
            self.assertRedirects(response, f'/profile/{author}/')
            self.assertEqual(self.user1.follower.count(), user1_followers)
            self.assertEqual(self.user1.following.count(), user1_followings)
            self.assertEqual(self.user2.follower.count(), user2_followers)
            self.assertEqual(self.user2.following.count(), user2_followings)
            self.assertEqual(self.user3.follower.count(), user3_followers)
            self.assertEqual(self.user3.following.count(), user3_followings)

    def test_views_subscriptions_users_can_follow_unfollow(self):
        """Проверка корректной работы подиски / отписки."""
        user1_followers = self.user1.follower.count()
        user1_followings = self.user1.following.count()
        user2_followers = self.user2.follower.count()
        user2_followings = self.user2.following.count()
        user3_followers = self.user3.follower.count()
        user3_followings = self.user3.following.count()
        # Первый user подписывается на второго.
        response = self.authorized_client1.get(self.url_follow2)
        author = self.user2.username
        user1_followers += 1
        user2_followings += 1
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Первый user подписывается на самого себя - нет изменений.
        response = self.authorized_client1.get(self.url_follow1)
        author = self.user1.username
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Первый user повторно подписывается на второго - нет изменений.
        response = self.authorized_client1.get(self.url_follow2)
        author = self.user2.username
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Второй user подписывается на первого.
        response = self.authorized_client2.get(self.url_follow1)
        author = self.user1.username
        user1_followings += 1
        user2_followers += 1
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Второй user подписывается на третьего.
        response = self.authorized_client2.get(self.url_follow3)
        author = self.user3.username
        user2_followers += 1
        user3_followings += 1
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Второй user отписывается от первого.
        response = self.authorized_client2.get(self.url_unfollow1)
        author = self.user1.username
        user1_followings -= 1
        user2_followers -= 1
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Второй user повторно отписывается от первого - нет изменений.
        response = self.authorized_client2.get(self.url_unfollow1)
        author = self.user1.username
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )
        # Второй user отписывается от самого себя - нет изменений.
        response = self.authorized_client2.get(self.url_unfollow2)
        author = self.user2.username
        self.check_subscriptions(
            response, user1_followers, user1_followings,
            user2_followers, user2_followings, user3_followers,
            user3_followings, author
        )

    def test_views_post_in_follow_list_of_subscribers(self):
        self.authorized_client2.get(self.url_follow1)
        self.authorized_client3.get(self.url_follow2)
        response = self.authorized_client2.get(reverse('posts:follow_index'))
        page = response.context['page_obj']
        self.assertIn(self.post, page)
        self.assertNotIn(self.post2, page)
        response = self.authorized_client3.get(reverse('posts:follow_index'))
        page = response.context['page_obj']
        with self.subTest(response=response):
            self.assertNotIn(self.post, page)
            self.assertIn(self.post2, page)
