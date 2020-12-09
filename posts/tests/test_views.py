import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.flatpages.models import FlatPage
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from posts import constants

from ..models import Group, Post


class StaticURLTests(TestCase):
    def setUp(self):
        self.site1 = Site.objects.filter()[0]
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
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
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
        cls.image = constants.uploaded
        cls.test_post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.test_group,
            image=constants.uploaded,
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


    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


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
            

    def paginator_posts_count(self, response):        
        self.count_check = response.context.get('paginator').count
        return self.count_check
  
    def test_posts_pages_show_correct_context(self):
        for template, reverse_name in self.posts_templates_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                if response.context.get('paginator'):
                    all_posts_count = Post.objects.count()
                    count_check = self.paginator_posts_count(response)
                    self.assertEqual(count_check, all_posts_count)
                    response_context = response.context.get('page')[0]
                else:
                    response_context = response.context.get('post')
                self.assertEqual(response_context.text, self.test_post.text)
                self.assertEqual(response_context.author, self.user)
                self.assertEqual(response_context.group, self.test_group)
                self.assertEqual(response_context.image.size, self.image.size)


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
        group2 = Group.objects.create(
            title='Тестовое сообщество2',
            slug='test-group2',
        )
        post2 = Post.objects.create(
            text='Тестовый пост2',
            author=self.user,
            group=group2,
        )
        
        newpost_pages = {
            'index': reverse('index'),
            'group_posts': reverse('group_posts',
            kwargs={'slug': group2.slug}),
        }
        
        for page, reverse_name in newpost_pages.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                response_context_0 = response.context.get('page')[0]
                self.assertEqual(response_context_0.pk, post2.pk)
                self.assertEqual(response_context_0.text, post2.text)
                self.assertEqual(response_context_0.author, self.user)
                self.assertEqual(response_context_0.group, post2.group)

                if page == 'group_posts':
                    posts = Post.objects.filter(group=post2.group).count()
                    paginator_posts = self.paginator_posts_count(response)
                    self.assertEqual(paginator_posts, posts)
                else:
                    posts = Post.objects.count()
                    paginator_posts = self.paginator_posts_count(response)
                    self.assertEqual(paginator_posts, posts)


    def test_newpost_not_in_another_group(self):
        group2 = Group.objects.create(
            title='Тестовое сообщество2',
            slug='test-group2',
        )
        post2 = Post.objects.create(
            text='Тестовый пост2',
            author=self.user,
            group=group2,
        )

        response = self.authorized_client.get(
            reverse('group_posts',
            kwargs={'slug': self.test_group.slug})
        )
        response_context_0 = response.context.get('page')[0].pk
        self.assertEqual(response_context_0, self.test_post.pk)
        posts = Post.objects.filter(group=self.test_post.group).count()
        paginator_posts = self.paginator_posts_count(response)
        self.assertEqual(paginator_posts, posts)


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

        index = response.context.get('paginator').page(1)
        posts_count = index.object_list.count() <= constants.posts_per_page
        self.assertTrue(posts_count)

        all_posts_count = Post.objects.count()
        paginator_posts_count = self.paginator_posts_count(response)
        self.assertEqual(all_posts_count, paginator_posts_count)


    def test_index_cache(self):
        self.assertEqual(Post.objects.count(), 1)
        response1 = self.client.get(reverse('index')).content
        Post.objects.all().delete()
        self.assertEqual(Post.objects.count(), 0)
        response2 = self.client.get(reverse('index')).content
        self.assertEqual(response1, response2)
        cache.clear()
        response3 = self.client.get(reverse('index')).content
        self.assertNotEqual(response1, response3)
