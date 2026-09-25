from django.db import models
from django.conf import settings
from blog.models import Blog, Comment

class SiteSetting(models.Model):
    site_name = models.CharField(max_length=100, default='Blogs Monkey')
    site_description = models.CharField(max_length=255, default='Modern blog publishing SaaS platform for writers, developers, and creators.')
    hero_headline = models.CharField(max_length=200, default='Publishing reimagined for modern creators.')
    hero_subheadline = models.TextField(default='Create, curate, and grow your audience with Blogs Monkey editorial experience.')
    allow_user_registration = models.BooleanField(default=True)
    require_approval_for_blogs = models.BooleanField(default=True, help_text='Require admin approval before user blogs are published.')
    maintenance_mode = models.BooleanField(default=False)
    contact_email = models.EmailField(default='sanskarkumar871@gamil.com')
    footer_text = models.TextField(default='© 2026 Blogs Monkey Inc. All rights reserved.')
    updated_at = models.DateTimeField(auto_now=True)


    def save(self, *args, **kwargs):
        # Singleton pattern enforcement
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f"Site Settings ({self.site_name})"


class ReportStatus(models.TextChoices):
    PENDING = 'pending', 'Pending Review'
    RESOLVED = 'resolved', 'Resolved'
    DISMISSED = 'dismissed', 'Dismissed'


class Report(models.Model):
    blog = models.ForeignKey(Blog, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE, null=True, blank=True, related_name='reports')
    reported_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reports_submitted')
    reason = models.TextField(max_length=500, help_text='Describe why this content violates community guidelines')
    status = models.CharField(max_length=20, choices=ReportStatus.choices, default=ReportStatus.PENDING, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        target = self.blog.title if self.blog else f"Comment #{self.comment_id}"
        return f"Report on '{target}' by {self.reported_by.username}"


class AIUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_usages')
    feature = models.CharField(max_length=50, db_index=True)  # 'chat', 'brainstorm', 'outline', 'format', 'explain', etc.
    model = models.CharField(max_length=100)
    prompt_tokens = models.PositiveIntegerField(default=0)
    completion_tokens = models.PositiveIntegerField(default=0)
    total_tokens = models.PositiveIntegerField(default=0)
    approx_cost = models.DecimalField(max_digits=10, decimal_places=6, default=0.0)
    status = models.CharField(max_length=20, default='success', db_index=True)  # 'success', 'error', 'rate_limited'
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Usage Record'
        verbose_name_plural = 'AI Usage Records'

    def __str__(self):
        return f"AIUsage ({self.feature}) by {self.user.username} at {self.created_at}"

