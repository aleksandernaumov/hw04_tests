from django import forms

from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text')
        labels = {
            'group': 'Выберите сообщество',
            'text': 'Заполните текст записи'
        }
        help_texts = {
            'group': 'Не обязательное поле',
            'text': 'Обязательное поле'
        }
