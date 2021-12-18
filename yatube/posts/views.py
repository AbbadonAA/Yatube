from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from yatube.settings import P_PER_L

from .forms import CommentForm, PostForm
from .models import Group, Post, Follow, User


def paginator_func(posts, per_list, request):
    """Паджинатор."""
    paginator = Paginator(posts, per_list)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return page_obj


@cache_page(20, key_prefix='index_page')
def index(request):
    """Рендер главной страницы."""
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_obj = paginator_func(posts, P_PER_L, request)
    context = {
        'page_obj': page_obj,
        'index': 'index',
    }
    return render(request, template, context)


def group_posts(request, slug):
    """Рендер страницы сообщества."""
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    page_obj = paginator_func(posts, P_PER_L, request)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    """Рендер страницы профайла."""
    template = 'posts/profile.html'
    user = get_object_or_404(User, username=username)
    posts = user.post.all()
    counter = posts.count()
    page_obj = paginator_func(posts, P_PER_L, request)
    following = False
    if request.user.is_authenticated:
        subscriptions = request.user.follower.values()
        list_subscriptions = [
            subscripted['author_id'] for subscripted in subscriptions
        ]
        following = True if user.id in list_subscriptions else False
    context = {
        'author': user,
        'counter': counter,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    """Рендер страницы поста."""
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, id=post_id)
    counter = post.author.post.count()
    title = post.text
    form = CommentForm(request.POST or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'counter': counter,
        'title': title,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Рендер страницы создания поста."""
    template = 'posts/create_post.html'
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', username=post.author)
    return render(request, template, {'form': form})


@login_required
def post_edit(request, post_id):
    """Рендер страницы редактирования поста."""
    template = 'posts/create_post.html'
    post = get_object_or_404(Post, id=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, template, {'form': form,
                                      'is_edit': True})


@login_required
def add_comment(request, post_id):
    """Добавление комментария к посту."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id)


@login_required
def follow_index(request):
    """Страница с постами авторов, на которых подписан user."""
    template = 'posts/follow.html'
    followings = request.user.follower.values()
    list_followings = [following['author_id'] for following in followings]
    posts = Post.objects.filter(author_id__in=list_followings)
    page_obj = paginator_func(posts, P_PER_L, request)
    context = {
        'page_obj': page_obj,
        'follow': 'follow',
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    post_author = User.objects.get(username=username)
    if request.user != post_author:
        subscriptions = request.user.follower.values()
        list_subscriptions = [
            subscripted['author_id'] for subscripted in subscriptions
        ]
        if post_author.id not in list_subscriptions:
            subscription = Follow(user=request.user, author=post_author)
            subscription.save()
            return redirect('posts:profile', username=username)
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Отписаться от автора."""
    post_author = User.objects.get(username=username)
    if request.user != post_author:
        subscriptions = request.user.follower.values()
        list_subscriptions = [
            subscripted['author_id'] for subscripted in subscriptions
        ]
        if post_author.id in list_subscriptions:
            unsubscribe = request.user.follower.get(author=post_author)
            unsubscribe.delete()
            return redirect('posts:profile', username=username)
        return redirect('posts:profile', username=username)
    return redirect('posts:profile', username=username)
