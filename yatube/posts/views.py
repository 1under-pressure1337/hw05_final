from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, Follow
from django.core.paginator import Paginator
from django.contrib.auth import get_user_model
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from yatube.settings import SHOWED_POSTS
from django.views.decorators.cache import cache_page

User = get_user_model()


# Главная страница
@cache_page(20, key_prefix='index_page')
def index(request):
    """Выводит шаблон главной страницы"""
    context = get_page_context(Post.objects.all(), request)
    return render(request, 'posts/index.html', context)


# View-функция для страницы сообщества:
def group_posts(request, slug):
    """Выводит шаблон с группами постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()[:SHOWED_POSTS]
    context = {
        'group': group,
        'posts': posts,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    author = get_object_or_404(User, username=username)
    user = request.user
    paginator = Paginator(author.posts.all(), SHOWED_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if user.is_authenticated:
        is_follower = Follow.objects.filter(user=user, author=author)
        if is_follower.exists():
            following = True
    following_context = {
        'user': user,
        'author': author,
        'page_obj': page_obj,
        'following': following
    }
    return render(request, 'posts/profile.html', following_context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = post.comments.select_related('author')
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


def get_page_context(queryset, request):
    paginator = Paginator(queryset, SHOWED_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'paginator': paginator,
        'page_number': page_number,
        'page_obj': page_obj,
    }


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            form.save()
            return redirect('posts:profile', request.user)
        return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    form = PostForm(request.POST or None, instance=post,
                    files=request.FILES or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
    context = {
        'form': form,
        'post': post,
        'is_edit': True,
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Информация о текущем пользователе доступна в переменной request.user."""
    user = request.user
    post = Post.objects.filter(author__following__user=user)
    page_obj = get_page_context(post, request)
    context = {
        'post': post,
    }
    context.update(page_obj)
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписаться на автора."""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    user = request.user
    following = user.follower.filter(author=author)
    following.delete()
    return redirect('posts:follow_index')
