from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.contrib.syndication.views import Feed
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.db import connection

from blog.models import Blog, Comment
from .models import SiteSetting, Report

class HealthCheckView(View):
    def get(self, request):
        db_ok = False
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                db_ok = True
        except Exception:
            db_ok = False

        status_code = 200 if db_ok else 500
        return JsonResponse({
            'status': 'healthy' if db_ok else 'unhealthy',
            'database': 'connected' if db_ok else 'disconnected',
            'version': '1.0.0'
        }, status=status_code)


class RobotsTxtView(View):
    def get(self, request):
        lines = [
            "User-agent: *",
            "Disallow: /admin/",
            "Disallow: /dashboard/",
            "Disallow: /api/",
            "Sitemap: " + request.build_absolute_uri('/sitemap.xml')
        ]
        return HttpResponse("\n".join(lines), content_type="text/plain")


class LatestBlogsFeed(Feed):
    title = "BlogSaaS - Latest Published Posts"
    link = "/"
    description = "Updates on new articles and tutorials published on BlogSaaS."

    def items(self):
        return Blog.published.order_by('-published_at')[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_pubdate(self, item):
        return item.published_at


@method_decorator(login_required, name='dispatch')
class ReportBlogView(View):
    def post(self, request, blog_id):
        blog = get_object_or_404(Blog, id=blog_id)
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "Please provide a reason for your report.")
            return redirect('blog:blog_detail', slug=blog.slug)

        Report.objects.create(
            blog=blog,
            reported_by=request.user,
            reason=reason
        )
        messages.success(request, "Thank you. Your report has been submitted to site administrators for review.")
        return redirect('blog:blog_detail', slug=blog.slug)


@method_decorator(login_required, name='dispatch')
class ReportCommentView(View):
    def post(self, request, comment_id):
        comment = get_object_or_404(Comment, id=comment_id)
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, "Please provide a reason for your report.")
            return redirect('blog:blog_detail', slug=comment.blog.slug)

        Report.objects.create(
            comment=comment,
            blog=comment.blog,
            reported_by=request.user,
            reason=reason
        )
        messages.success(request, "Thank you. The comment has been flagged for admin review.")
        return redirect('blog:blog_detail', slug=comment.blog.slug)
