from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from .. import constants
from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()

class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        form_data = {
            'text': 'Создаем новую запись в группе',
            'group': self.test_group.id,
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 1)
        self.assertEqual(Post.objects.get(id=1).text, form_data['text'])
        self.assertEqual(Post.objects.get(id=1).group.id, form_data['group'])
        self.assertEqual(Post.objects.get(id=1).author.id, self.test_user.id)


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
        self.assertRedirects(response, reverse('post', kwargs=kwargs))
        self.assertEqual(
            Post.objects.get(id=test_post.id).text,
            form_data_edit['text']
        )
        self.assertEqual(
            Post.objects.get(id=test_post.id).group.id,
            form_data_edit['group']
        )
        self.assertEqual(Post.objects.count(), 1)


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
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)


    def test_edit_post_guest(self):
        form_data_edit = {
            'text': 'Исправленный гостем текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
            )

        kwargs = {'username': 'test_user', 'post_id': test_post.id}

        response = self.client.post(
            reverse('post_edit', kwargs=kwargs),
            data=form_data_edit,
            follow=True
        )
        self.assertNotEqual(
            Post.objects.get(id=test_post.id).text,
            form_data_edit['text']
        )


    def test_edit_post_not_author(self):
        form_data_edit = {
            'text': 'Исправленный не автором текст записи',
            'group': self.test_group.id,
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.test_user,
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
        self.assertNotEqual(
            Post.objects.get(id=test_post.id).text,
            form_data_edit['text']
        )
