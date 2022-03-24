from django.contrib.auth import get_user_model
from http import HTTPStatus
from django.test import TestCase, Client
from django.urls import reverse
from posts.models import Post, Group

User = get_user_model()


class URLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.group_slug = cls.group.slug
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовая пост',
            group=cls.group,
        )
        cls.post_id = cls.post.pk
        cls.user_nick = cls.user.username

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(
            username='HasNoName'
        )
        self.user_2 = User.objects.get(
            username='auth'
        )
        self.authorized_client = Client()
        self.authorized_client_author = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_client_author.force_login(self.user_2)
        self.ok = HTTPStatus.OK.value
        self.nf = HTTPStatus.NOT_FOUND.value
        self.found = HTTPStatus.FOUND.value
        self.test_urls = {
            '/': [self.ok, 'posts/index.html'],
            f'/group/{URLTests.group_slug}/':
                [self.ok, 'posts/group_list.html'],
            f'/profile/{URLTests.user_nick}/':
                [self.ok, 'posts/profile.html'],
            f'/posts/{URLTests.post_id}/':
                [self.ok, 'posts/post_detail.html'],
            '/create/': [self.ok, 'users/login.html'],
            f'/posts/{URLTests.post_id}/edit/': [self.ok, 'users/login.html']

        }
        self.test_urls_for_authenticated = {
            f'/posts/{URLTests.post_id}/edit/':
                [self.ok, 'posts/post_detail.html'],
            '/create/': [self.ok, 'posts/create_post.html']
        }

    def test_pages_free_to_visit(self):
        for url, data in self.test_urls.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertEqual(response.status_code, data[0])
                self.assertTemplateUsed(
                    response, data[1],
                    'используется не тот шаблон'
                )

    def test_pages_for_authenticated(self):
        for url, data in self.test_urls_for_authenticated.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url, follow=True)
                self.assertEqual(response.status_code, data[0])
                self.assertTemplateUsed(
                    response, data[1],
                    'используется не тот шаблон'
                )

    def test_pages_for_authors(self):
        response = self.authorized_client_author.get(
            f'/posts/{URLTests.post_id}/edit/'
        )
        self.assertEqual(response.status_code, self.ok)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_not_found_page(self):
        response = self.authorized_client.get('/not_found/')
        self.assertEqual(response.status_code, self.nf)

    def test_redirect_anonymous_users(self):
        links_to_try_enter = ['/create/', f'/posts/{URLTests.post_id}/edit/']
        for url in links_to_try_enter:
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(
                    response, reverse('users:login') + f'?next={url}')

    def test_redirect_non_author(self):
        response = self.authorized_client.get(
            f'/posts/{URLTests.post_id}/edit/',
            follow=True
        )
        self.assertRedirects(
            response,
            reverse('posts:post_detail', kwargs={
                'post_id': f'{URLTests.post_id}'}))
