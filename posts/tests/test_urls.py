from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase

from ..models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.site1 = Site(pk=1)
        self.site1.save()
        self.aboutauthor_page = FlatPage.objects.create(url='/about-author/')
        self.aboutspec_page = FlatPage.objects.create(url='/about-spec/')
        self.aboutauthor_page.sites.add(self.site1)
        self.aboutspec_page.sites.add(self.site1)


    def test_flatpages_exist(self):
        flatpages = ('/about-author/', '/about-spec/')

        for flatpage in flatpages:
            with self.subTest():
                response = self.guest_client.get(flatpage)
                self.assertEqual(response.status_code, 200)


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = get_user_model().objects.create(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        Group.objects.create(
            title='Тестовое сообщество',
            slug='test-group',
            description='test-group',
        )
        Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            pk=100,
        )


    def setUp(self):
        self.template_url_names = {
            'index.html': '/',
            'group.html': '/group/test-group/',
            'newpost.html': '/new/',
            'profile.html': '/testuser/',
            'post.html': '/testuser/100/',
            'newpost.html': '/testuser/100/edit/',
        }


    def test_url_exist(self):
        for template, url in self.template_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)


    def test_url_uses_correct_template(self):
        for template, url in self.template_url_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)


    def test_login_required_urls_redirect_anonymous_on_loginpage(self):
        login_required_urls = {
            '/new/': '/auth/login/?next=/new/',
            '/testuser/100/edit/':
            '/auth/login/?next=/testuser/100/edit/',
        }

        for url, redirect_url in login_required_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url, follow=True)
                self.assertRedirects(response, (redirect_url))


    def test_post_edit_not_author(self):
        not_author = get_user_model().objects.create(username='not_author')
        not_author_client = Client()
        not_author_client.force_login(not_author)
        response = not_author_client.get('/testuser/100/edit/')
        self.assertRedirects(response, ('/testuser/100/'))
