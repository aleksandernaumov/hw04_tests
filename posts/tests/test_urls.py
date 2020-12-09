from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post


class PostsUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user_model().objects.create(username='testuser')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-group',
            description='test-group',
        )
        
        cls.test_post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            pk=100,
        )
        
        cls.site1 = Site.objects.filter()[0]

        var_flatpages = {
            'aboutauthor_page': '/about-author/',
            'aboutspec_page': '/about-spec/',
        }

        for cls.var, flatpage in var_flatpages.items():
            cls.var = FlatPage.objects.create(url=flatpage)
            cls.var.sites.add(cls.site1)

        cls.template_guest_access_urls = {
            'index.html': reverse('index'),
            'posts/group.html': reverse(
                'group_posts',
                kwargs = {'slug': cls.test_group.slug}
            ),
            'posts/profile.html': reverse(
                'profile', 
                kwargs = {'username': cls.user}
            ),
            'posts/post.html': reverse(
                'post', 
                kwargs = {'username': cls.user,
                'post_id': cls.test_post.id}
            ),
            'flatpages/default.html': reverse('about-author'),
            'flatpages/default.html': reverse('about-spec'),
        }

        cls.template_login_required_urls = {
            'posts/newpost.html': reverse('new_post'),
            'posts/newpost.html': reverse(
                'post_edit', 
                kwargs = {'username': cls.user,
                'post_id': cls.test_post.id}
            ),
        }


    def test_guest_access_urls_exist(self):
        for template, url in self.template_guest_access_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 200)


    def test_login_required_urls_exist(self):
        for template, url in self.template_login_required_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, 200)


    def test_guest_access_urls_uses_correct_template(self):
        for template, url in self.template_guest_access_urls.items():
            with self.subTest(url=url):
                response = self.client.get(url)
                self.assertTemplateUsed(response, template)


    def test_login_required_urls_uses_correct_template(self):
        for template, url in self.template_login_required_urls.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)


    def test_login_required_urls_redirect_anonymous_on_loginpage(self):
        for var, redirect_url in self.template_login_required_urls.items():
            with self.subTest(url=redirect_url):
                response = self.client.get(redirect_url, follow=True)
                login_page=reverse('login')               
                self.assertRedirects(
                    response, 
                    (f'{login_page}?next={redirect_url}')
                )


    def test_post_edit_not_author(self):
        not_author = get_user_model().objects.create(username='not_author')
        not_author_client = Client()
        not_author_client.force_login(not_author)
        response = not_author_client.get(
            reverse(
            'post_edit', 
            kwargs = {'username': self.user,
            'post_id': self.test_post.id})
        )
        self.assertEquals(response.status_code, 404)


    def test_page_404(self):
        for template, url in self.template_guest_access_urls.items():
            with self.subTest(url=url):
                not_existing_url = 'not_existing' + url
                response = self.client.get(not_existing_url)
                self.assertEqual(response.status_code, 404)
