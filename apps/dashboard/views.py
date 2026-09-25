from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.http import HttpResponse, JsonResponse

from blog.models import Blog, BlogStatus, Category, Tag, Bookmark, Like
from blog.forms import BlogForm
from accounts.models import User, UserStatus, UserRole
from content.models import SiteSetting, Report, ReportStatus

def admin_required(view_func):
    """Decorator ensuring current user is an admin."""
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_site_admin:
            messages.error(request, "Access denied. Admin privileges required.")
            return redirect('dashboard:home')
        return view_func(request, *args, **kwargs)
    return _wrapped_view




# --- USER DASHBOARD VIEWS ---

@method_decorator(login_required, name='dispatch')
class UserDashboardView(View):
    template_name = 'dashboard/home.html'

    def get(self, request):
        user = request.user
        user_blogs = Blog.objects.filter(author=user)
        
        total_blogs = user_blogs.count()
        published_count = user_blogs.filter(status=BlogStatus.PUBLISHED).count()
        draft_count = user_blogs.filter(status=BlogStatus.DRAFT).count()
        pending_count = user_blogs.filter(status=BlogStatus.PENDING_REVIEW).count()
        rejected_count = user_blogs.filter(status=BlogStatus.REJECTED).count()
        
        total_views = user_blogs.aggregate(Sum('view_count'))['view_count__sum'] or 0
        total_likes = Like.objects.filter(blog__author=user).count()

        recent_blogs = user_blogs.select_related('category').order_by('-updated_at')[:5]

        context = {
            'total_blogs': total_blogs,
            'published_count': published_count,
            'draft_count': draft_count,
            'pending_count': pending_count,
            'rejected_count': rejected_count,
            'total_views': total_views,
            'total_likes': total_likes,
            'recent_blogs': recent_blogs,
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class UserBlogListView(View):
    template_name = 'dashboard/blog_list.html'

    def get(self, request):
        status_filter = request.GET.get('status')
        query = request.GET.get('q')

        user_blogs = Blog.objects.filter(author=request.user).select_related('category')

        if status_filter:
            user_blogs = user_blogs.filter(status=status_filter)

        if query:
            user_blogs = user_blogs.filter(Q(title__icontains=query) | Q(excerpt__icontains=query))

        context = {
            'blogs': user_blogs.order_by('-updated_at'),
            'current_status': status_filter or 'all',
            'query': query or '',
            'statuses': BlogStatus.choices
        }
        return render(request, self.template_name, context)


@method_decorator(login_required, name='dispatch')
class BlogCreateView(View):
    template_name = 'dashboard/blog_form.html'

    def get(self, request):
        form = BlogForm()
        return render(request, self.template_name, {'form': form, 'is_edit': False})

    def post(self, request):
        form = BlogForm(request.POST, request.FILES)
        action = request.POST.get('action') # 'draft' or 'submit'
        if form.is_valid():
            blog = form.save(commit=False)
            blog.author = request.user
            
            # Check site setting for approval requirement or admin role
            settings = SiteSetting.get_settings()
            if action == 'submit':
                if not settings.require_approval_for_blogs or request.user.is_site_admin:
                    blog.status = BlogStatus.PUBLISHED
                    blog.published_at = timezone.now()
                    msg = "Your post has been published successfully!"
                else:
                    blog.status = BlogStatus.PENDING_REVIEW
                    msg = "Your post has been submitted for admin review."
            else:
                blog.status = BlogStatus.DRAFT
                msg = "Draft saved successfully!"

            blog.save()
            form.save_m2m()
            messages.success(request, msg)
            return redirect('dashboard:blog_list')

        return render(request, self.template_name, {'form': form, 'is_edit': False})


@method_decorator(login_required, name='dispatch')
class BlogEditView(View):
    template_name = 'dashboard/blog_form.html'

    def get(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if blog.author != request.user and not request.user.is_site_admin:
            raise PermissionDenied("You cannot edit another user's post.")
        form = BlogForm(instance=blog)
        return render(request, self.template_name, {'form': form, 'blog': blog, 'is_edit': True})

    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if blog.author != request.user and not request.user.is_site_admin:
            raise PermissionDenied("You cannot edit another user's post.")

        form = BlogForm(request.POST, request.FILES, instance=blog)
        action = request.POST.get('action')
        if form.is_valid():
            blog = form.save(commit=False)
            settings = SiteSetting.get_settings()
            
            if action == 'submit':
                if not settings.require_approval_for_blogs or request.user.is_site_admin:
                    blog.status = BlogStatus.PUBLISHED
                    if not blog.published_at:
                        blog.published_at = timezone.now()
                    msg = "Post updated and published!"
                else:
                    blog.status = BlogStatus.PENDING_REVIEW
                    msg = "Post updated and submitted for review."
            elif action == 'publish' and request.user.is_site_admin:
                blog.status = BlogStatus.PUBLISHED
                if not blog.published_at:
                    blog.published_at = timezone.now()
                msg = "Post published directly by admin!"
            else:
                # Keep as draft if already draft, or if explicitly requested draft
                if blog.status == BlogStatus.REJECTED:
                    blog.status = BlogStatus.DRAFT
                msg = "Post changes saved successfully!"

            blog.save()
            form.save_m2m()
            messages.success(request, msg)
            return redirect('dashboard:blog_list')

        return render(request, self.template_name, {'form': form, 'blog': blog, 'is_edit': True})


@method_decorator(login_required, name='dispatch')
class BlogDeleteView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if blog.author != request.user and not request.user.is_site_admin:
            raise PermissionDenied("You cannot delete another user's post.")
        blog.delete()
        messages.success(request, "Post deleted successfully.")
        return redirect('dashboard:blog_list')


@method_decorator(login_required, name='dispatch')
class BlogArchiveView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        if blog.author != request.user and not request.user.is_site_admin:
            raise PermissionDenied("You cannot archive another user's post.")
        
        if blog.status == BlogStatus.ARCHIVED:
            blog.status = BlogStatus.DRAFT
            messages.success(request, f"Article '{blog.title}' unarchived and moved to drafts.")
        else:
            blog.status = BlogStatus.ARCHIVED
            messages.success(request, f"Article '{blog.title}' archived successfully.")
        
        blog.save()
        return redirect('dashboard:blog_list')


@method_decorator(login_required, name='dispatch')
class SubmitBlogForReviewView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk, author=request.user)
        settings = SiteSetting.get_settings()
        if not settings.require_approval_for_blogs or request.user.is_site_admin:
            blog.status = BlogStatus.PUBLISHED
            blog.published_at = timezone.now()
            messages.success(request, "Post published successfully.")
        else:
            blog.status = BlogStatus.PENDING_REVIEW
            messages.success(request, "Post submitted for review.")
        blog.save()
        return redirect('dashboard:blog_list')


@method_decorator(login_required, name='dispatch')
class UserBookmarksView(View):
    template_name = 'dashboard/bookmarks.html'

    def get(self, request):
        bookmarks = Bookmark.objects.filter(user=request.user).select_related('blog', 'blog__author', 'blog__category')
        return render(request, self.template_name, {'bookmarks': bookmarks})


@method_decorator(login_required, name='dispatch')
class UserLikesView(View):
    template_name = 'dashboard/likes.html'

    def get(self, request):
        likes = Like.objects.filter(user=request.user).select_related('blog', 'blog__author', 'blog__category')
        return render(request, self.template_name, {'likes': likes})


# --- ADMIN OPERATIONAL DASHBOARD VIEWS ---

@method_decorator([login_required, admin_required], name='dispatch')
class AdminDashboardView(View):
    template_name = 'dashboard/admin/home.html'

    def get(self, request):
        total_users = User.objects.count()
        total_blogs = Blog.objects.count()
        published_blogs = Blog.objects.filter(status=BlogStatus.PUBLISHED).count()
        pending_blogs = Blog.objects.filter(status=BlogStatus.PENDING_REVIEW).count()
        total_reports = Report.objects.filter(status=ReportStatus.PENDING).count()
        total_views = sum(b.view_count for b in Blog.objects.all())

        pending_queue = Blog.objects.filter(status=BlogStatus.PENDING_REVIEW).select_related('author', 'category')[:5]
        recent_users = User.objects.order_by('-date_joined')[:5]
        recent_reports = Report.objects.filter(status=ReportStatus.PENDING).select_related('blog', 'reported_by')[:5]

        context = {
            'total_users': total_users,
            'total_blogs': total_blogs,
            'published_blogs': published_blogs,
            'pending_blogs': pending_blogs,
            'total_reports': total_reports,
            'total_views': total_views,
            'pending_queue': pending_queue,
            'recent_users': recent_users,
            'recent_reports': recent_reports,
        }
        return render(request, self.template_name, context)


@method_decorator([login_required, admin_required], name='dispatch')
class AdminModerationQueueView(View):
    template_name = 'dashboard/admin/moderation_queue.html'

    def get(self, request):
        pending_blogs = Blog.objects.filter(status=BlogStatus.PENDING_REVIEW).select_related('author', 'category').order_by('created_at')
        return render(request, self.template_name, {'pending_blogs': pending_blogs})


@method_decorator([login_required, admin_required], name='dispatch')
class AdminApproveBlogView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        blog.status = BlogStatus.PUBLISHED
        blog.rejection_reason = ''
        if not blog.published_at:
            blog.published_at = timezone.now()
        blog.save()
        messages.success(request, f"Post '{blog.title}' approved and published.")
        return redirect('dashboard:admin_moderation')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminRejectBlogView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        reason = request.POST.get('rejection_reason', '').strip()
        blog.status = BlogStatus.REJECTED
        blog.rejection_reason = reason or 'Content did not meet platform guidelines.'
        blog.save()
        messages.warning(request, f"Post '{blog.title}' rejected.")
        return redirect('dashboard:admin_moderation')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminChangeBlogStatusView(View):
    """Direct status transition view for admins (e.g. unpublish, archive, publish, draft)."""
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        new_status = request.POST.get('status')
        if new_status in BlogStatus.values:
            blog.status = new_status
            if new_status == BlogStatus.PUBLISHED and not blog.published_at:
                blog.published_at = timezone.now()
            blog.save()
            messages.success(request, f"Post status updated to '{blog.get_status_display()}'.")
        else:
            messages.error(request, "Invalid status choice.")
        return redirect('dashboard:admin_blogs')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminManageBlogsView(View):
    template_name = 'dashboard/admin/blogs.html'

    def get(self, request):
        query = request.GET.get('q')
        status_filter = request.GET.get('status')
        blogs = Blog.objects.select_related('author', 'category').order_by('-created_at')

        if query:
            blogs = blogs.filter(Q(title__icontains=query) | Q(author__username__icontains=query))
        if status_filter:
            blogs = blogs.filter(status=status_filter)

        return render(request, self.template_name, {'blogs': blogs, 'statuses': BlogStatus.choices})


@method_decorator([login_required, admin_required], name='dispatch')
class AdminToggleFeatureBlogView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        blog.is_featured = not blog.is_featured
        blog.save()
        state = "featured" if blog.is_featured else "unfeatured"
        messages.success(request, f"Post '{blog.title}' marked as {state}.")
        return redirect('dashboard:admin_blogs')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminToggleTrendingBlogView(View):
    def post(self, request, pk):
        blog = get_object_or_404(Blog, pk=pk)
        blog.is_trending = not blog.is_trending
        blog.save()
        state = "trending" if blog.is_trending else "normal"
        messages.success(request, f"Post '{blog.title}' set to {state}.")
        return redirect('dashboard:admin_blogs')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminManageUsersView(View):
    template_name = 'dashboard/admin/users.html'

    def get(self, request):
        query = request.GET.get('q')
        users = User.objects.all().order_by('-date_joined')
        if query:
            users = users.filter(Q(username__icontains=query) | Q(email__icontains=query))
        return render(request, self.template_name, {'users': users})


@method_decorator([login_required, admin_required], name='dispatch')
class AdminToggleUserStatusView(View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user == request.user:
            messages.error(request, "You cannot suspend your own account!")
            return redirect('dashboard:admin_users')

        if user.status == UserStatus.ACTIVE:
            user.status = UserStatus.SUSPENDED
            messages.warning(request, f"User '{user.username}' has been suspended.")
        else:
            user.status = UserStatus.ACTIVE
            messages.success(request, f"User '{user.username}' reactivated.")
        user.save()
        return redirect('dashboard:admin_users')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminManageCategoriesView(View):
    template_name = 'dashboard/admin/categories.html'

    def get(self, request):
        categories = Category.objects.annotate(blog_count=Count('blogs'))
        return render(request, self.template_name, {'categories': categories})

    def post(self, request):
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        icon_name = request.POST.get('icon_name', 'folder').strip()

        if name:
            Category.objects.create(name=name, description=description, icon_name=icon_name)
            messages.success(request, f"Category '{name}' created successfully.")
        else:
            messages.error(request, "Category name is required.")
        return redirect('dashboard:admin_categories')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminManageTagsView(View):
    template_name = 'dashboard/admin/tags.html'

    def get(self, request):
        tags = Tag.objects.annotate(blog_count=Count('blogs'))
        return render(request, self.template_name, {'tags': tags})

    def post(self, request):
        name = request.POST.get('name', '').strip()
        if name:
            Tag.objects.create(name=name)
            messages.success(request, f"Tag '{name}' created successfully.")
        else:
            messages.error(request, "Tag name is required.")
        return redirect('dashboard:admin_tags')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminSiteSettingsView(View):
    template_name = 'dashboard/admin/site_settings.html'

    def get(self, request):
        site_obj = SiteSetting.get_settings()
        return render(request, self.template_name, {'site_settings': site_obj})

    def post(self, request):
        site_obj = SiteSetting.get_settings()
        site_obj.site_name = request.POST.get('site_name', site_obj.site_name)
        site_obj.site_description = request.POST.get('site_description', site_obj.site_description)
        site_obj.hero_headline = request.POST.get('hero_headline', site_obj.hero_headline)
        site_obj.hero_subheadline = request.POST.get('hero_subheadline', site_obj.hero_subheadline)
        site_obj.allow_user_registration = 'allow_user_registration' in request.POST
        site_obj.require_approval_for_blogs = 'require_approval_for_blogs' in request.POST
        site_obj.maintenance_mode = 'maintenance_mode' in request.POST
        site_obj.contact_email = request.POST.get('contact_email', site_obj.contact_email)
        site_obj.footer_text = request.POST.get('footer_text', site_obj.footer_text)
        site_obj.save()

        messages.success(request, "Site settings updated successfully.")
        return redirect('dashboard:admin_settings')


@method_decorator([login_required, admin_required], name='dispatch')
class AdminManageReportsView(View):
    template_name = 'dashboard/admin/reports.html'

    def get(self, request):
        reports = Report.objects.select_related('blog', 'reported_by').order_by('-created_at')
        return render(request, self.template_name, {'reports': reports})

    def post(self, request, pk):
        report = get_object_or_404(Report, pk=pk)
        action = request.POST.get('action') # 'resolve' or 'dismiss'
        if action == 'resolve':
            report.status = ReportStatus.RESOLVED
            messages.success(request, "Report marked as resolved.")
        elif action == 'dismiss':
            report.status = ReportStatus.DISMISSED
            messages.info(request, "Report dismissed.")
        report.save()
        return redirect('dashboard:admin_reports')
