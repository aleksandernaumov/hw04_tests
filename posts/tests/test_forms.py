from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Post


class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()


    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create(
            username='test_user'
        )
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)


    def test_form_labels(self):
        form_labels = {
            'text': 'Заполните текст записи',
            'group': 'Выберите сообщество'
        }

        for field, label in form_labels.items():
            with self.subTest(label=label):
                field_label = PostFormTests.form.fields[field].label
                self.assertEqual(field_label, label)


    def test_form_help_texts(self):
        form_help_texts = {
            'text': 'Обязательное поле',
            'group': 'Не обязательное поле'
        }

        for field, help_text in form_help_texts.items():
            with self.subTest(help_text=help_text):
                field_help_text = PostFormTests.form.fields[field].help_text
                self.assertEqual(field_help_text, help_text)


    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый текст записи',
            'group': '',
        }

        response = self.authorized_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/')
        self.assertEqual(Post.objects.count(), posts_count+1)


    def test_edit_post(self):
        form_data_edit = {
            'text': 'Исправленный тестовый текст записи',
            'group': '',
        }
        test_post = Post.objects.create(
            text='Тестовый текст записи',
            author=self.user,
            pk=100,
        )

        response = self.authorized_client.post(
            reverse(
                'post_edit',
                kwargs={'username': 'test_user', 'post_id': '100'}),
            data=form_data_edit,
            follow=True
        )
        self.assertRedirects(response, '/test_user/100/')
        self.assertEqual(
            Post.objects.get(pk=100).text,
            'Исправленный тестовый текст записи'
        )
