from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from .. import constants
from ..models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        self.site1 = Site.objects.get(pk=1)
        self.aboutauthor_page = FlatPage.objects.create(
            url='/about-author/',
            title='Об авторе title',
            content='Об авторе контент'
        )
        self.aboutspec_page = FlatPage.objects.create(
            url='/about-spec/',
            title='О технологии title',
            content='О технологии контент'
        )
        self.aboutauthor_page.sites.add(self.site1)
        self.aboutspec_page.sites.add(self.site1)


    def test_about_author_show_correct_context(self):
        response = self.client.get(reverse('about-author'))
        self.assertEqual(
            self.aboutauthor_page.content,
            response.context.get('flatpage').content
        )


    def test_about_spec_show_correct_context(self):
        response = self.client.get(reverse('about-spec'))
        self.assertEqual(
            self.aboutspec_page.content,
            response.context.get('flatpage').content
        )


class ViewPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        User = get_user_model()
        cls.user = User.objects.create(
            username='test_user'
        )
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
            group=cls.test_group,
        )

        cls.posts_templates_pages = {
            'index.html': reverse('index'),            
            'posts/group.html': (
                reverse('group_posts', kwargs={'slug': cls.test_group.slug})
            ),
            'posts/profile.html': (
                reverse('profile', kwargs={'username': cls.user.username})
            ),
            'posts/post.html': (
                reverse('post', kwargs={'username': cls.user.username,
                'post_id': cls.test_post.id})
            ),
        }

        cls.new_edit_pages = (
            reverse('new_post'),
            reverse('post_edit',
            kwargs={'username': cls.user.username,
            'post_id': cls.test_post.id}),
        )


    def test_posts_pages_uses_correct_template(self):        
        for template, reverse_name in self.posts_templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template) 


    def test_new_edit_pages_uses_correct_template(self):
        for reverse_name in self.new_edit_pages:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, 'posts/newpost.html') 


    def test_posts_pages_show_correct_context(self):
        for template, reverse_name in self.posts_templates_pages.items():
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                if response.context.get('paginator'):
                    count_check = response.context.get('paginator').count
                    self.assertEqual(count_check, 1)
                    response_context = response.context.get('page')[0]
                else:
                    response_context = response.context.get('post')                    
                self.assertEqual(response_context.text, self.test_post.text)
                self.assertEqual(response_context.author, self.user)
                self.assertEqual(response_context.group, self.test_group)


    def test_new_edit_pages_show_correct_context(self):
        for reverse_name in self.new_edit_pages:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'group': forms.fields.ChoiceField,      
                'text': forms.fields.CharField,
            }
            
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    field = response.context.get('form').fields.get(value)
                    self.assertIsInstance(field, expected)


    def test_newpost_on_index_group(self):
        test_group2 = Group.objects.create(
            title='Тестовое сообщество2',
            slug='test-group2',
        )
        test_post2 = Post.objects.create(
            text='Тестовый пост2',
            author=self.user,
            group=test_group2,
        )
        
        newpost_pages = (
            reverse('index'),
            reverse('group_posts',
            kwargs={'slug': test_group2.slug}),
        )
        
        for reverse_name in newpost_pages:
            with self.subTest(reverse_name=reverse_name):
               response = self.authorized_client.get(reverse_name)
               response_context_0 = response.context.get('page')[0].pk
               self.assertEqual(response_context_0, test_post2.pk)


    def test_newpost_not_in_another_group(self):
        test_group2 = Group.objects.create(
            title='Тестовое сообщество2',
            slug='test-group2',
        )
        test_post2 = Post.objects.create(
            text='Тестовый пост2',
            author=self.user,
            group=test_group2,
        )

        response = self.authorized_client.get(
            reverse('group_posts',
            kwargs={'slug': self.test_group.slug})
        )
        response_context_0 = response.context.get('page')[0].pk
        self.assertNotEqual(response_context_0, test_post2.pk)


    def test_posts_quantity_on_index(self):
        for n in range(1, 20):
            Post.objects.create(
            text=1,
            author=self.user,
            pk=n+1,
        )

        response = self.authorized_client.get(reverse('index'))
        posts_on_page = response.context.get('paginator').per_page
        self.assertEqual(posts_on_page, constants.posts_per_page)

        posts_on_index = response.context.get('paginator').page(1)
        posts_quantity = len(posts_on_index) <= constants.posts_per_page
        self.assertTrue(posts_quantity)
