from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from . import api_views

app_name = 'dashboard'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'blogs', api_views.BlogViewSet, basename='api_blog')
router.register(r'categories', api_views.CategoryViewSet, basename='api_category')
router.register(r'tags', api_views.TagViewSet, basename='api_tag')

urlpatterns = [
    # User Dashboard Routes
    path('', views.UserDashboardView.as_view(), name='home'),
    path('blogs/', views.UserBlogListView.as_view(), name='blog_list'),
    path('blogs/create/', views.BlogCreateView.as_view(), name='blog_create'),
    path('blogs/<int:pk>/edit/', views.BlogEditView.as_view(), name='blog_edit'),
    path('blogs/<int:pk>/delete/', views.BlogDeleteView.as_view(), name='blog_delete'),
    path('blogs/<int:pk>/archive/', views.BlogArchiveView.as_view(), name='blog_archive'),
    path('blogs/<int:pk>/submit/', views.SubmitBlogForReviewView.as_view(), name='blog_submit'),
    path('bookmarks/', views.UserBookmarksView.as_view(), name='bookmarks'),
    path('likes/', views.UserLikesView.as_view(), name='likes'),

    # Custom Operational Admin Dashboard Routes
    path('admin/', views.AdminDashboardView.as_view(), name='admin_home'),
    path('admin/moderation/', views.AdminModerationQueueView.as_view(), name='admin_moderation'),
    path('admin/blogs/', views.AdminManageBlogsView.as_view(), name='admin_blogs'),
    path('admin/blogs/<int:pk>/approve/', views.AdminApproveBlogView.as_view(), name='admin_blog_approve'),
    path('admin/blogs/<int:pk>/reject/', views.AdminRejectBlogView.as_view(), name='admin_blog_reject'),
    path('admin/blogs/<int:pk>/status/', views.AdminChangeBlogStatusView.as_view(), name='admin_blog_status'),
    path('admin/blogs/<int:pk>/toggle-feature/', views.AdminToggleFeatureBlogView.as_view(), name='admin_blog_toggle_feature'),
    path('admin/blogs/<int:pk>/toggle-trending/', views.AdminToggleTrendingBlogView.as_view(), name='admin_blog_toggle_trending'),
    path('admin/users/', views.AdminManageUsersView.as_view(), name='admin_users'),
    path('admin/users/<int:pk>/toggle-status/', views.AdminToggleUserStatusView.as_view(), name='admin_user_toggle_status'),
    path('admin/categories/', views.AdminManageCategoriesView.as_view(), name='admin_categories'),
    path('admin/tags/', views.AdminManageTagsView.as_view(), name='admin_tags'),
    path('admin/settings/', views.AdminSiteSettingsView.as_view(), name='admin_settings'),
    path('admin/reports/', views.AdminManageReportsView.as_view(), name='admin_reports'),
    path('admin/reports/<int:pk>/action/', views.AdminManageReportsView.as_view(), name='admin_report_action'),

    # REST API v1 Endpoints & JWT Authentication
    path('api/v1/', include(router.urls)),
    path('api/v1/search/autocomplete/', api_views.SearchAutocompleteAPIView.as_view(), name='api_search_autocomplete'),
    path('api/v1/stats/', api_views.DashboardStatsAPIView.as_view(), name='api_stats'),
    path('api/v1/format-article/', api_views.FormatArticleAPIView.as_view(), name='api_format_article'),

    # AI Feature Routes (OpenRouter Gateway & AI Companion)
    path('api/v1/ai/chat/', api_views.AIChatAPIView.as_view(), name='api_ai_chat'),
    path('api/v1/ai/brainstorm/', api_views.AIBrainstormAPIView.as_view(), name='api_ai_brainstorm'),
    path('api/v1/ai/outline/', api_views.AIOutlineAPIView.as_view(), name='api_ai_outline'),
    path('api/v1/ai/selection/', api_views.AISelectionActionAPIView.as_view(), name='api_ai_selection'),
    path('api/v1/ai/stats/', api_views.AIUsageStatsAPIView.as_view(), name='api_ai_stats'),

    path('api/v1/auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

