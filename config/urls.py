import os
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

# pyrefly: ignore [missing-import]
from content.sitemaps import BlogSitemap, CategorySitemap, TagSitemap

sitemaps = {
    'blogs': BlogSitemap,
    'categories': CategorySitemap,
    'tags': TagSitemap,
}

# Configurable Admin Route (defaults to 'admin/')
ADMIN_PATH = os.environ.get('ADMIN_URL_PATH', 'admin/').strip('/') + '/'

urlpatterns = [
    # Standard / Configurable Django Admin
    path(ADMIN_PATH, admin.site.urls),

    # Web App Modules
    path('', include('blog.urls', namespace='blog')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('', include('content.urls', namespace='content')),

    # SEO Sitemap XML
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
