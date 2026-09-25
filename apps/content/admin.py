from django.contrib import admin
from .models import SiteSetting, Report

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'allow_user_registration', 'require_approval_for_blogs', 'maintenance_mode', 'updated_at')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('blog', 'reported_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reason', 'blog__title', 'reported_by__username')
