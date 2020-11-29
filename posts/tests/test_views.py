from django import forms
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.site1 = Site(pk=1)
        self.site1.save()
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
        response = self.guest_client.get(reverse('about-author'))
        self.assertEqual(
            self.aboutauthor_page.content,
            response.context.get('flatpage').content
        )


    def test_about_spec_show_correct_context(self):
        response = self.guest_client.get(reverse('about-spec'))
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
        Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.test_group,
            pk=101,
        )


    def test_pages_uses_correct_template(self):
        templates_pages_names = {
            'index.html': reverse('index'),
            'newpost.html': reverse('new_post'),
            'group.html': (
                reverse('group_posts', kwargs={'slug': 'test-group'})
            ),
        }
        
        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template) 


    def test_page_postslist_show_correct_context(self):
        templates_with_postslist_reversnames = (
            reverse('index'),
            reverse('group_posts', kwargs={'slug': 'test-group'}),
            reverse('profile', kwargs={'username': 'test_user'}),
        )
        
        for reverse_name in templates_with_postslist_reversnames:
            with self.subTest():
                response = self.authorized_client.get(reverse_name)
                post_text_0 = response.context.get('page')[0].text
                post_author_0 = response.context.get('page')[0].author.username
                post_group_0 = response.context.get('page')[0].group.title
                self.assertEqual(post_text_0, 'Тестовый пост')
                self.assertEqual(post_author_0, 'test_user')
                self.assertEqual(post_group_0, 'Тестовое сообщество')


    def test_post_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('post', kwargs={'username': 'test_user', 'post_id': '101'})
        )
        self.assertEqual(
            response.context.get('post').text,
            'Тестовый пост'
        )
        self.assertEqual(
            response.context.get('post').author.username,
            'test_user'
        )
        self.assertEqual(
            response.context.get('post').group.title,
            'Тестовое сообщество'
        )


    def test_new_or_edit_post_show_correct_context(self):
        response1 = self.authorized_client.get(reverse('new_post'))
        response2 = self.authorized_client.get(
            reverse('post_edit',
            kwargs={'username': 'test_user', 'post_id': '101'})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,      
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response1.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
                form_field = response2.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


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
        test_post3 = Post.objects.create(
            text='Тестовый пост3',
            author=self.user,
            group=self.test_group,
        )

        response = self.authorized_client.get(
            reverse('group_posts', kwargs={'slug': 'test-group2'})
        )
        post_text_2 = response.context.get('page')[0].text
        post_group_2 = response.context.get('page')[0].group.title
        self.assertNotEqual(post_text_2, 'Тестовый пост3')
        self.assertEqual(post_group_2, 'Тестовое сообщество2')


    def test_posts_quantity_on_index(self):
        for n in range(1, 20):
            Post.objects.create(
            text=n+1,
            author=self.user,
            pk=n+1,
        )

        response = self.authorized_client.get(reverse('index'))
        posts_on_page = response.context.get('page')
        posts_quantity = len(posts_on_page) <= 10
        self.assertTrue(posts_quantity)
