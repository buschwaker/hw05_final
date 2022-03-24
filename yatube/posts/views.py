from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User, Follow
from django.contrib.auth.decorators import login_required
from .forms import PostForm, CommentForm


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
        'index': True,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    all_user_posts = author.posts.all()
    paginator = Paginator(all_user_posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    count = all_user_posts.count()
    if request.user.is_authenticated:
        if author.pk in list(
                following.author.pk
                for following in request.user.follower.all()):
            following = True
        else:
            following = False
        context = {
            'author': author,
            'page_obj': page_obj,
            'count': count,
            'following': following,
        }
        return render(request, 'posts/profile.html', context)
    context = {
        'author': author,
        'page_obj': page_obj,
        'count': count,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    context = {
        'post': post,
        'form': form,
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            new = form.save(commit=False)
            new.author = request.user
            new.save()
            return redirect('posts:profile', request.user.username)
        return render(request, 'posts/create_post.html', {'form': form})
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    is_edit = True
    post = get_object_or_404(Post, pk=post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)
    if form.is_valid():
        post.text = form.cleaned_data['text']
        post.group = form.cleaned_data['group']
        post.save()
        return redirect('posts:post_detail', post_id)
    context = {'form': form, 'is_edit': is_edit}
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
    user = request.user
    post = Post.objects.filter(
        author__id__in=user.follower.values('author_id')
    )
    paginator = Paginator(post, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'follow': True, }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user_to_follow = get_object_or_404(User, username=username)
    if user_to_follow.pk in list(
            following.author.pk for following in request.user.follower.all()):
        return redirect('posts:follow_index')
    if user_to_follow == request.user:
        return redirect('posts:follow_index')
    Follow.objects.create(
        user=request.user,
        author=user_to_follow)
    return redirect('posts:follow_index')


@login_required
def profile_unfollow(request, username):
    user_to_unfollow = get_object_or_404(User, username=username)
    if user_to_unfollow == request.user:
        return redirect('posts:follow_index')
    if user_to_unfollow.pk not in list(
            following.author.pk for following in request.user.follower.all()):
        return redirect('posts:follow_index')
    Follow.objects.get(
        user=request.user,
        author=user_to_unfollow
    ).delete()
    return redirect('posts:follow_index')
