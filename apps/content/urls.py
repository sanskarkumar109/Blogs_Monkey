from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    path('health/', views.HealthCheckView.as_view(), name='health_check'),
    path('robots.txt', views.RobotsTxtView.as_view(), name='robots_txt'),
    path('feed/', views.LatestBlogsFeed(), name='rss_feed'),
    path('report/blog/<int:blog_id>/', views.ReportBlogView.as_view(), name='report_blog'),
    path('report/comment/<int:comment_id>/', views.ReportCommentView.as_view(), name='report_comment'),
]
