from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Group(models.Model):
    title = models.CharField('Сообщество', max_length=200)
    slug = models.SlugField(
        'Ссылка (slug)', unique=True, max_length=50
    )
    description = models.TextField(
        'Описание', help_text='Краткое описание сообщества'
    )

    class Meta:
        verbose_name_plural = 'Группы'

    def __str__(self):
        return self.title


class Post(models.Model):
    text = models.TextField('Текст', help_text='Обязательное поле')
    pub_date = models.DateTimeField(
        'Дата публикации', auto_now_add=True
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='posts', verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group, on_delete=models.SET_NULL,
        blank=True, null=True, related_name='posts',
        verbose_name='Сообщество', help_text='Не обязательное поле'
    )
    image = models.ImageField(
        upload_to='posts/', blank=True, null=True,
        verbose_name='Изображение', help_text='Не обязательное поле'
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name_plural = 'Записи'

    def __str__(self):
        post_date = self.pub_date
        post_author = self.author
        post_text = self.text[:20]
        return f'{post_author} - {post_date:%d-%m-%Y} - {post_text} ...'


class Comment(models.Model):
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name='comments',
        verbose_name='Запись в сообществе', help_text='Обязательное поле'
    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name='comments', verbose_name='Автор'
    )
    text = models.TextField('Текст', help_text='Обязательное поле')
    created = models.DateTimeField(
        'Дата комментария', auto_now_add=True
    )

    class Meta:
        ordering = ['-created']
        verbose_name_plural = 'Комментарии'

    def __str__(self):
        commentdate = self.created
        commentauthor = self.author
        commenttext = self.text[:20]
        return f'{commentauthor} - {commentdate:%d-%m-%Y} - {commenttext} ...'
