from django.urls import reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.db.models import Q, F, Count
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponse
from django.contrib import messages

from .models import Blog, BlogStatus, Category, Tag, Comment, Like, Bookmark
from accounts.models import User
from .forms import CommentForm

class HomeView(View):
    template_name = 'blog/home.html'

    def get(self, request):
        # Optimized query with select_related & prefetch_related
        published_blogs = Blog.published.select_related('author', 'author__profile', 'category').prefetch_related('tags')
        
        featured_blogs = published_blogs.filter(is_featured=True)[:3]
        if not featured_blogs.exists():
            featured_blogs = published_blogs[:3]
            
        trending_blogs = published_blogs.filter(is_trending=True)[:4]
        if not trending_blogs.exists():
            trending_blogs = published_blogs.order_by('-view_count')[:4]
            
        latest_blogs = published_blogs.order_by('-published_at')[:6]
        categories = Category.objects.annotate(blog_count=Count('blogs', filter=Q(blogs__status=BlogStatus.PUBLISHED)))
        tags = Tag.objects.annotate(blog_count=Count('blogs', filter=Q(blogs__status=BlogStatus.PUBLISHED)))[:15]
        popular_authors = User.objects.annotate(published_count=Count('blogs', filter=Q(blogs__status=BlogStatus.PUBLISHED))).filter(published_count__gt=0).select_related('profile').order_by('-published_count')[:6]

        context = {
            'featured_blogs': featured_blogs,
            'trending_blogs': trending_blogs,
            'latest_blogs': latest_blogs,
            'categories': categories,
            'tags': tags,
            'popular_authors': popular_authors,
        }
        return render(request, self.template_name, context)


class BlogListView(ListView):
    model = Blog
    template_name = 'blog/blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 9

    def get_queryset(self):
        queryset = Blog.published.select_related('author', 'author__profile', 'category').prefetch_related('tags')
        
        query = self.request.GET.get('q')
        category_slug = self.request.GET.get('category')
        tag_slug = self.request.GET.get('tag')
        sort = self.request.GET.get('sort', 'latest')

        if query:
            queryset = queryset.filter(
                Q(title__icontains=query) |
                Q(excerpt__icontains=query) |
                Q(content__icontains=query) |
                Q(author__username__icontains=query)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)

        if sort == 'popular':
            queryset = queryset.order_by('-view_count')
        elif sort == 'oldest':
            queryset = queryset.order_by('published_at')
        else:
            queryset = queryset.order_by('-published_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['popular_tags'] = Tag.objects.annotate(blog_count=Count('blogs', filter=Q(blogs__status=BlogStatus.PUBLISHED)))[:20]
        context['current_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_tag'] = self.request.GET.get('tag', '')
        context['current_sort'] = self.request.GET.get('sort', 'latest')
        return context


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'
    context_object_name = 'blog'
    slug_field = 'slug'

    def get_queryset(self):
        # Allow author or admin to preview non-published blogs, otherwise restrict to published
        user = self.request.user
        if user.is_authenticated and (user.is_site_admin or user.role == 'admin'):
            return Blog.objects.select_related('author', 'author__profile', 'category').prefetch_related('tags', 'comments__author')
        elif user.is_authenticated:
            return Blog.objects.filter(Q(status=BlogStatus.PUBLISHED) | Q(author=user)).select_related('author', 'author__profile', 'category').prefetch_related('tags', 'comments__author')
        return Blog.published.select_related('author', 'author__profile', 'category').prefetch_related('tags', 'comments__author')

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # Increment view count atomically
        Blog.objects.filter(pk=self.object.pk).update(view_count=F('view_count') + 1)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog = self.object
        
        # Fetch related blogs in same category or with matching tags
        related_blogs = Blog.published.filter(category=blog.category).exclude(id=blog.id).select_related('author', 'category')[:3]
        
        # User interactions (like & bookmark status)
        is_liked = False
        is_bookmarked = False
        if self.request.user.is_authenticated:
            is_liked = Like.objects.filter(blog=blog, user=self.request.user).exists()
            is_bookmarked = Bookmark.objects.filter(blog=blog, user=self.request.user).exists()

        context['related_blogs'] = related_blogs
        context['comments'] = blog.comments.filter(is_approved=True, parent=None).order_by('-created_at')
        context['comment_form'] = CommentForm()
        context['is_liked'] = is_liked
        context['is_bookmarked'] = is_bookmarked
        context['like_count'] = blog.likes.count()
        return context


class CategoryDetailView(DetailView):
    model = Category
    template_name = 'blog/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        blogs = Blog.published.filter(category=category).select_related('author', 'category').prefetch_related('tags')
        context['blogs'] = blogs
        return context


class TagDetailView(DetailView):
    model = Tag
    template_name = 'blog/tag_detail.html'
    context_object_name = 'tag'
    slug_field = 'slug'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tag = self.object
        blogs = Blog.published.filter(tags=tag).select_related('author', 'category').prefetch_related('tags')
        context['blogs'] = blogs
        return context


class AuthorProfileView(DetailView):
    model = User
    template_name = 'blog/author_profile.html'
    context_object_name = 'author'
    slug_field = 'username'
    slug_url_kwarg = 'username'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = self.object
        published_blogs = Blog.published.filter(author=author).select_related('category', 'author').prefetch_related('tags')
        liked_blogs = Blog.published.filter(likes__user=author).select_related('category', 'author').prefetch_related('tags')
        
        bookmarked_blogs = []
        if self.request.user.is_authenticated and self.request.user == author:
            bookmarked_blogs = Blog.published.filter(bookmarks__user=author).select_related('category', 'author').prefetch_related('tags')

        context['blogs'] = published_blogs
        context['liked_blogs'] = liked_blogs
        context['bookmarked_blogs'] = bookmarked_blogs
        context['total_views'] = sum(b.view_count for b in published_blogs)
        return context


@method_decorator(login_required, name='dispatch')
class ToggleLikeView(View):
    def post(self, request, blog_id):
        blog = get_object_or_404(Blog, id=blog_id)
        like, created = Like.objects.get_or_create(blog=blog, user=request.user)
        if not created:
            like.delete()
            liked = False
        else:
            liked = True
        
        count = blog.likes.count()
        if request.headers.get('HX-Request'):
            icon_svg = '<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />'
            fill_class = "fill-rose-500 text-rose-500" if liked else "fill-none text-slate-500"
            html = f'<button hx-post="{reverse("blog:toggle_like", kwargs={"blog_id": blog.id})}" hx-swap="outerHTML" class="flex items-center space-x-2 px-4 py-2 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-rose-300 dark:hover:border-rose-900 transition text-sm font-medium"><svg class="w-5 h-5 {fill_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor">{icon_svg}</svg><span>{count}</span></button>'
            return HttpResponse(html)
        return JsonResponse({'liked': liked, 'count': count})


@method_decorator(login_required, name='dispatch')
class ToggleBookmarkView(View):
    def post(self, request, blog_id):
        blog = get_object_or_404(Blog, id=blog_id)
        bookmark, created = Bookmark.objects.get_or_create(blog=blog, user=request.user)
        if not created:
            bookmark.delete()
            bookmarked = False
        else:
            bookmarked = True

        if request.headers.get('HX-Request'):
            fill_class = "fill-indigo-500 text-indigo-500" if bookmarked else "fill-none text-slate-500"
            html = f'<button hx-post="{reverse("blog:toggle_bookmark", kwargs={"blog_id": blog.id})}" hx-swap="outerHTML" class="p-2.5 rounded-xl border border-slate-200 dark:border-slate-800 hover:border-indigo-300 dark:hover:border-indigo-900 transition text-slate-500"><svg class="w-5 h-5 {fill_class}" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"/></svg></button>'
            return HttpResponse(html)
        return JsonResponse({'bookmarked': bookmarked})


@method_decorator(login_required, name='dispatch')
class AddCommentView(View):
    def post(self, request, blog_id):
        blog = get_object_or_404(Blog, id=blog_id)
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.blog = blog
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    comment.parent = Comment.objects.get(id=parent_id, blog=blog)
                except Comment.DoesNotExist:
                    pass
            comment.save()
            messages.success(request, "Your comment has been published.")
        else:
            messages.error(request, "Failed to submit comment. Please check your message.")
        return redirect('blog:blog_detail', slug=blog.slug)
