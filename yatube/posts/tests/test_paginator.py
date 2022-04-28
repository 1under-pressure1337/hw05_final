from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Group, Post, User


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testusername')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание группы',
            slug='test-slug',
        )
        cls.posts = []
        for i in range(0, 15):
            cls.posts.append(Post.objects.create(
                text=f'Текст{i}',
                author=cls.user,
                group=cls.group,
            ))

    def setUp(self):
        self.guest_client = Client()

    def test_first_page_contains_ten_records(self):
        """Тест паджинатора - 10 постов на странице 1."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page)
                self.assertEqual(len(response.context.get('page_obj')), 10)

    def test_last_page_contains_three_records(self):
        """Тест паджинатора  - 5 постов на странице 2."""
        pages = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test-slug'}),
            reverse('posts:profile',
                    kwargs={'username': PaginatorViewsTest.user.username}
                    )
        ]
        for page in pages:
            with self.subTest(page=page):
                response = self.guest_client.get(page + '?page=2')
                self.assertEqual(len(response.context.get('page_obj')), 5)
