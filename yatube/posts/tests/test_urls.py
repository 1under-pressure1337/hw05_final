from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from http import HTTPStatus
from posts.models import Group, Post, Follow

from django.core.cache import cache

from django.urls import reverse

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testusername')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='testname')
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user)
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user)
        cache.clear()

    def test_post_urls_status_client(self):
        """URL-адрес доступен гостю."""
        url_names = {
            '/': HTTPStatus.OK,
            f'/group/{self.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/': HTTPStatus.OK,
            f'/posts/{self.post.id}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for url, code in url_names.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, code)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/': 'posts/index.html',
            '/create/': 'posts/create_post.html',
            f'/group/{self.group.slug}/': 'posts/group_list.html',
            f'/profile/{self.user.username}/': 'posts/profile.html',
            f'/posts/{self.post.pk}/': 'posts/post_detail.html',
            f'/posts/{self.post.pk}/edit/': 'posts/create_post.html',
        }
        for url, template in templates_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_post_edit_url_exists_for_author(self):
        """Страница post_edit доступна автору."""
        response = self.author_client.get(f'/posts/{self.post.pk}/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_url_redirect_anonymous_user_on_login(self):
        """
        Страница post_create перенаправит анонимного
        пользователя на страницу логина.
        """
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )

    def test_follow_pages_available(self):
        """
        Авторизированный пользователь подписывается и удаляет подписки.
        """
        urls = [
            reverse('posts:profile_follow',
                    kwargs={'username': self.user}),
            reverse('posts:profile_unfollow',
                    kwargs={'username': self.user})
        ]
        for url in urls:
            response = self.authorized_client.post(url)
            with self.subTest(url=url):
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_in_feed(self):
        """Новая запись появляется в ленте того, на кого подписан."""
        new_author = User.objects.create(username='new_author')
        Follow.objects.create(user=self.user, author=new_author)
        post = Post.objects.create(author=new_author)
        response = self.authorized_client.get(reverse('posts:follow_index'))
        object = response.context.get('page_obj').object_list
        self.assertNotIn(post, object)
