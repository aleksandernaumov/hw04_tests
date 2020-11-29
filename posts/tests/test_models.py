from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()

class PostFormTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = User.objects.create(
            username='test_user'
        )
        cls.test_group = Group.objects.create(
            title='Тестовое сообщество',
            slug='test-group',
            description='test-group',
        )
        cls.test_post = Post.objects.create(
            text='Тестовый пост',
            pub_date='21.11.2020',
            author=cls.test_user,
            group=cls.test_group,
        )


    def test_group_verbose_name(self):
        test_group = PostFormTest.test_group
        field_verboses = {
            'title': 'Сообщество',
            'slug': 'Ссылка (slug)',
            'description': 'Описание',
        }

        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_group._meta.get_field(value).verbose_name, expected)


    def test_post_verbose_name(self):
        test_post = PostFormTest.test_post
        field_verboses = {
            'text': 'Текст',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Сообщество',
        }
        
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).verbose_name, expected)


    def test_group_help_text(self):
        test_group = PostFormTest.test_group
        help_text = test_group._meta.get_field('description').help_text
        self.assertEqual(help_text, 'Краткое описание сообщества')


    def test_post_help_text(self):
        test_post = PostFormTest.test_post
        field_verboses = {
            'text': 'Обязательное поле',
            'group': 'Не обязательное поле',
        }
        
        for value, expected in field_verboses.items():
            with self.subTest(value=value):
                self.assertEqual(
                    test_post._meta.get_field(value).help_text, expected)


    def test_group_name_is_title_field(self):
        test_group = PostFormTest.test_group
        expected_group_name = test_group.title
        self.assertEquals(expected_group_name, str(test_group))


    def test_post_text_is_20_symbols(self):
        test_post = PostFormTest.test_post
        a = test_post.author
        d = test_post.pub_date
        t = test_post.text[:20]
        expected_post_text = f'{a} - {d:%d-%m-%Y} - {t} ...'
        self.assertEquals(expected_post_text, str(test_post))
