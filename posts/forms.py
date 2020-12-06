from django import forms

from . import constants
from .models import Post


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('group', 'text')
        labels = constants.form_post_labels
