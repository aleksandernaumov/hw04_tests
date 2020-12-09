import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from posts import constants

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.form = PostForm()
        cls.test_user = User.objects.create(
            username='test_user'
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.test_user)
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-group',
            description='test-group',
        )
        cls.image = constants.small_gif


    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()


    def test_form_labels(self):
        for field, label in constants.form_post_labels.items():
            with self.subTest(label=label):
                field_label = PostFormTests.form.fields[field].label
                self.assertEqual(field_label, label)


    def test_form_help_texts(self):
        for field, help_text in constants.form_post_help_texts.items():
            with self.subTest(help_text=help_text):
                field_help_text = PostFormTests.form.fields[field].help_text
                self.assertEqual(field_help_text, help_text)


    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Создаем новую запись в группе',
            'group': self.test_group.id,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertEqual(response.status_code, 200)
        last_object = Post.objects.filter().order_by('-id')[0]
        self.assertEqual(last_object.text, form_data['text'])
        self.assertEqual(last_object.group, self.test_group)
        self.assertEqual(last_object.author, self.test_user)


    def test_edit_post(self):
        form_data_edit = {
            'text': 'Исправленный тестовый текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
        )

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = self.authorized_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertEqual(Post.objects.count(), 1)
        self.assertRedirects(response, reverse('post', kwargs=kwargs))
        self.assertEqual(test_post.text, form_data_edit['text'])
        self.assertEqual(test_post.group, self.test_group)
        self.assertEqual(test_post.author, self.test_user)


    def test_create_post_guest(self):
        form_data = {
            'text': 'Гость пытается создать новую запись в группе',
            'group': self.test_group.id,
        }

        response = self.client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(response.status_code, 200)


    def test_edit_post_guest(self):
        form_data_edit = {
            'text': 'Исправленный гостем текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
            group=self.test_group,
        )

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = self.client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertNotEqual(test_post.text, form_data_edit['text'])
        self.assertEqual(test_post.group, self.test_group)
        self.assertEqual(test_post.author, self.test_user)


    def test_edit_post_not_author(self):
        form_data_edit = {
            'text': 'Исправленный не автором текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
            group=self.test_group,
        )

        not_author_user = User.objects.create(
            username='not_author'
        )
        not_author_client = Client()
        not_author_client.force_login(not_author_user)

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = not_author_client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        test_post.refresh_from_db()
        self.assertNotEqual(test_post.text, form_data_edit['text'])
        self.assertEqual(test_post.group, self.test_group)
        self.assertEqual(test_post.author, self.test_user)


    def test_create_post_with_image(self):
        posts_count = Post.objects.count()
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Тестовый текст',
            'image': constants.uploaded,
        }
        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count+1)
        self.assertRedirects(response, reverse('index'))
