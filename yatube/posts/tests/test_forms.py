from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, Comment
from posts.models import User
from http.client import OK

import shutil
import tempfile

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small_1.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='testusername')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            description='Описание группы',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(PostFormsTests.user)

    def test_create_post(self):
        '''Тест создания поста.'''
        posts_count = Post.objects.count()
        form_data = {'text': 'Текст записанный в форму',
                     'group': self.group.id,
                     'image': self.uploaded
                     }
        response = self.authorized_client.post(reverse('posts:post_create'),
                                               data=form_data,
                                               follow=True)
        new_post = Post.objects.order_by('pk').last()
        self.assertEqual(response.status_code, OK)
        self.assertFalse(Post.objects.filter(
                         text='Текст записанный в форму',
                         group=1,
                         author=self.user
                         ).exists())
        self.assertEqual(Post.objects.count(),
                         posts_count)
        self.assertEqual(new_post.image.name,
                         'posts/' + form_data['image'].name)

    def test_edit_post(self):
        """Тест редактирования поста."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост',
            'group': self.group.id
        }
        response = self.author_client.post(
            reverse('posts:post_edit',
                    kwargs={'post_id': self.post.pk}),
            data=form_data, follow=True)
        self.assertEqual(
            Post.objects.count(), posts_count)
        num_post = response.context['post']
        text = num_post.text
        self.assertEqual(text, self.post.text)
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk}
        ))

    def test_non_authorize_client_comment(self):
        """Неавторизированный пользователь не может комментировать посты."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Текст комментария'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'users:login') + '?next=' + reverse(
            'posts:add_comment', kwargs={'post_id': self.post.id}))
        self.assertEqual(Comment.objects.count(), comments_count)

    def test_succesful_comment_appear_in_page(self):
        """После успешной отправки комментарий появляется на странице поста."""
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Тестовый текст комментария',
            'author': self.post.author.username
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.id}),
            data=form_data,
            follow=True
        )
        self.authorized_client.get(
            reverse('posts:post_detail', kwargs={'post_id': self.post.id}),
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        latest_comment = Comment.objects.get(pk=self.post.id)
        self.assertEqual(latest_comment.text, form_data['text'])
        self.assertEqual(latest_comment.author.username, form_data['author'])
