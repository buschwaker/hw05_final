from django.forms import ModelForm
from .models import Post, Comment
from django.utils.translation import ugettext_lazy as _


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ['text', 'group', 'image']
        labels = {
            'text': _('Текст поста'),
            'group': _('Группа')
        }
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост')
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['text', ]
