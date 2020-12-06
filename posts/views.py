from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpResponseNotFound
from django.shortcuts import get_object_or_404, redirect, render

from . import constants
from .forms import PostForm
from .models import Group, Post, User


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, constants.posts_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'index.html',
        {'page': page, 'paginator': paginator}
    )


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    paginator = Paginator(posts, constants.posts_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/group.html',
        {'page': page, 'paginator': paginator, 'group': group}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('index')
    return render(request, 'posts/newpost.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    posts = author.posts.all()
    paginator = Paginator(posts, constants.posts_per_page)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(
        request,
        'posts/profile.html',
        {'page': page,
         'paginator': paginator,
         'author': author}
    )


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author.username != username:
        return HttpResponseNotFound('<h1>Page not found</h1>')
    return render(
        request, 'posts/post.html', {'post': post, 'author': post.author}
    )


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return HttpResponseNotFound('<h1>Page not found</h1>')

    form = PostForm(request.POST or None, instance=post)

    if form.is_valid():
        form.save()
        return redirect('post', username=username, post_id=post_id)
    return render(
        request, 'posts/newpost.html',
        {'form': form, 'post': post}
    )
