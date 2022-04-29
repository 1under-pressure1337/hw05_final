from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Group, Post, Follow
from http import HTTPStatus


User = get_user_model()


class PostPagesTests(TestCase):
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
            text='Тестовый текст',
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    # Проверяем используемые шаблоны
    def test_pages_uses_correct_template(self):
        """View-классы используют ожидаемые HTML-шаблоны."""
        # Собираем в словарь пары "имя_html_шаблона: reverse(name)"
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug': 'test-slug'}
                    ): 'posts/group_list.html',
            reverse('posts:profile',
                    kwargs={'username': 'testusername'}
                    ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}
                    ): 'posts/post_detail.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}
                    ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html'
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_post = response.context['page_obj'][0]
        post_author_1 = first_post.author
        post_text_1 = first_post.text
        self.assertEqual(post_author_1, self.post.author)
        self.assertEqual(post_text_1, self.post.text)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list.html сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': 'test-slug'}))
        first_post = response.context['page_obj'][0]
        post_author_1 = first_post.author
        post_text_1 = first_post.text
        self.assertEqual(post_author_1, self.post.author)
        self.assertEqual(post_text_1, self.post.text)

    def test_new_post_not_in_wrong_group(self):
        """Пост не попал в группу, для которой не был предназначен"""
        post = Post.objects.get(pk=1)
        response = self.authorized_client.get(
            reverse(
                'posts:group_list', kwargs={'slug': self.group.slug}
            )
        )
        self.assertIn(post, response.context['page_obj'].object_list)

    def test_cache_index_page(self):
        """Проверка кеширования главной страницы."""
        response = self.guest_client.get(reverse('posts:index'))
        object1 = response.content
        self.new_post = Post.objects.create(
            author=self.user,
            text='Текст не попадет в кэш',
            group=self.group,
        )
        response_1 = self.guest_client.get(reverse('posts:index'))
        self.assertEqual(object1, response_1.content)

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
        self.assertIn(post, object)
