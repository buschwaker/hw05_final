from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from http import HTTPStatus
from django.urls import reverse
from posts.models import Post, Comment

User = get_user_model()


class PostCreateTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')

    def setUp(self):
        self.ok = HTTPStatus.OK.value
        self.user = User.objects.get(
            username='auth'
        )
        self.guest_user = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.response_post = self.authorized_client.post(
            reverse('posts:post_create'),
            data={'text': 'Текст из формы'},
            follow=True
        )

    def test_create_form(self):
        tasks_count = Post.objects.count()
        post = Post.objects.get(pk=1)
        self.assertEqual(post.text, 'Текст из формы')
        self.assertEqual(post.author, PostCreateTests.user)
        self.assertEqual(
            tasks_count,
            1,
            'создано больше одного поста'
        )
        self.assertEqual(self.response_post.status_code, self.ok)

    def test_edit_form(self):
        response_get_1 = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        post_text = response_get_1.context['form']['text'].value()
        post = Post.objects.get(text=post_text)
        id_1 = post.pk
        response_post_2 = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': '1'}),
            data={'text': 'Текст из формы редактированный'},
            follow=True
        )
        response_get_2 = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': '1'}))
        post_edited_text = response_get_2.context['form']['text'].value()
        post = Post.objects.get(text=post_edited_text)
        id_2 = post.pk
        self.assertEqual(response_post_2.status_code, self.ok)
        self.assertEqual(
            id_1,
            id_2,
            'id постов не совпадают'
        )
        self.assertNotEqual(
            post,
            post_edited_text,
            'тексты постов не совпадают'
        )

    def test_comment_form_authorised(self):
        count_before_comment = Comment.objects.count()
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data={'text': 'Комментарий к первому посту 1'},
            follow=True
        )
        self.assertTrue(Comment.objects.filter(
            text='Комментарий к первому посту 1',
            author__username='auth',
            post__pk=1).exists())
        self.assertEqual(Comment.objects.count(), count_before_comment + 1)

    def test_comment_form_unauthorised(self):
        count_before_comment = Comment.objects.count()
        self.guest_user.post(
            reverse('posts:add_comment', kwargs={'post_id': '1'}),
            data={'text': 'Комментарий к первому посту 2'},
            follow=True
        )
        self.assertFalse(Comment.objects.filter(
            text='Комментарий к первому посту 2').exists())
        self.assertEqual(Comment.objects.count(), count_before_comment)
