import shutil
import tempfile

from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django import forms
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group, Comment, Follow

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostTests(TestCase):
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
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user_to_follow = User.objects.create(username='user_to_follow')
        cls.non_sub = User.objects.create(
            username='non_sub'
        )
        cls.sub = User.objects.create(username='sub')
        cls.user = User.objects.create(
            username='auth',
        )
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group,
            image=uploaded,
        )
        for i in range(1, 15):
            Post.objects.create(
                author=cls.user,
                text='Тестовый пост',
                group=cls.group,
                image=uploaded,
            )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='Test comment'
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.user = User.objects.get(
            username='auth'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_sub = Client()
        self.authorized_client_sub.force_login(PostTests.sub)
        self.authorized_non_sub = Client()
        self.authorized_non_sub.force_login(PostTests.non_sub)

    def post_obj_asserts(self, post):
        self.assertEqual(post.text, PostTests.post.text)
        self.assertEqual(post.author.username, PostTests.user.username)
        self.assertEqual(post.group.title, PostTests.group.title)

    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            reverse('posts:main_page'): 'posts/index.html',
            reverse(
                'posts:group_page',
                kwargs={'slug': 'test'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username': 'auth'}
            ): 'posts/profile.html',
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}): 'posts/post_detail.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_edit',
                    kwargs={'post_id': '15'}): 'posts/create_post.html',

        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_home_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:main_page'))
        post = response.context['page_obj'][0]
        self.post_obj_asserts(post)
        self.assertIsNotNone(post.image)

    def test_group_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_page',
                    kwargs={'slug': 'test'}
                    )
        )
        group = response.context['group']
        post = response.context['page_obj'][0]
        self.post_obj_asserts(post)
        self.assertEqual(group.title, PostTests.group.title)
        self.assertEqual(group.description, PostTests.group.description)
        self.assertIsNotNone(post.image)

    def test_profile_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': 'auth'}
                    )
        )
        author = response.context['author']
        post = response.context['page_obj'][0]
        count = response.context['count']
        self.post_obj_asserts(post)
        self.assertEqual(author.username, PostTests.user.username)
        self.assertEqual(count, 15)
        self.assertIsNotNone(post.image)

    def test_post_detail_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    kwargs={'post_id': '1'}
                    )
        )
        post = response.context['post']
        comment = response.context['comments'][0]
        self.assertEqual(comment.text, PostTests.comment.text)
        self.assertEqual(post.text, PostTests.post.text)
        self.assertEqual(post.id, 1)
        self.assertIsNotNone(post.image)

    def test_create_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context['form'].fields.get(value)
                self.assertIsInstance(form, expected)

    def test_edit_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': '1'})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        self.assertTrue(response.context['is_edit'])
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form = response.context['form'].fields.get(value)
                self.assertIsInstance(form, expected)

    def test_paginator_ten_records(self):
        paginator_list = [
            reverse('posts:main_page'),
            reverse('posts:group_page', kwargs={'slug': 'test'}),
            reverse('posts:profile', kwargs={'username': 'auth'}),
        ]
        for route in paginator_list:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(len(response.context['page_obj']), 10)
                response = self.client.get(route + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 5)

    def test_post_with_group(self):
        group_test = Group.objects.create(slug='test_2')
        Post.objects.create(
            author=PostTests.user,
            text='Пост с группой',
            group=group_test,
        )
        response_get_1 = self.authorized_client.get(
            reverse('posts:main_page'))
        response_get_2 = self.authorized_client.get(
            reverse('posts:group_page',
                    kwargs={'slug': 'test_2'}))
        response_get_3 = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': 'auth'}))
        responses = [response_get_1, response_get_2, response_get_3]
        for response in responses:
            with self.subTest(response=response):
                self.assertIn(
                    'Пост с группой',
                    response.context['page_obj'][0].text)

    def test_posts_from_another_group(self):
        response_get_another_group = self.authorized_client.get(
            reverse('posts:group_page',
                    kwargs={'slug': 'test'}))
        for post_from_another_group in (
                response_get_another_group.context['page_obj']
        ):
            with self.subTest(
                    post_from_another_group=post_from_another_group
            ):
                self.assertNotEqual(
                    post_from_another_group.text,
                    'Пост с группой'
                )

    def test_main_page_cache(self):
        cache.clear()
        post_to_delete = Post.objects.create(
            text='Post ready to be deleted',
            author=self.user,)
        response = self.authorized_client.get(reverse('posts:main_page'))
        post_to_delete.delete()
        self.assertIn(post_to_delete.text,
                      response.content.decode("utf-8"))
        cache.clear()
        response = self.authorized_client.get(reverse('posts:main_page'))
        self.assertNotIn(post_to_delete.text,
                         response.content.decode("utf-8"))

    def test_follow_view(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': PostTests.user_to_follow}))
        self.assertTrue(
            Follow.objects.filter(
                user=self.user,
                author=PostTests.user_to_follow,
            ).exists()
        )

    def test_unfollow_view(self):
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostTests.user_to_follow}))
        self.assertFalse(
            Follow.objects.filter(
                user=self.user,
                author=PostTests.user_to_follow,
            ).exists())

    def test_if_sub_see_post(self):
        self.authorized_client_sub.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        response_sub = self.authorized_client_sub.get(
            reverse('posts:follow_index')
        )
        self.assertIn(
            PostTests.post.text,
            response_sub.content.decode("utf-8"), 'не нашлось')

    def test_if_non_sub_see_post(self):
        response_non_sub = self.authorized_non_sub.get(
            reverse('posts:follow_index')
        )
        self.assertNotIn(
            PostTests.post.text,
            response_non_sub.content.decode("utf-8"))
