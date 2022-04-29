from django import forms
from posts.models import Post, Comment, Follow


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            "image": ("Картинка к посту",)
        }


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)


class FollowForm(forms.ModelForm):
    class Meta:
        model = Follow
        fields = ('user', 'author',)
