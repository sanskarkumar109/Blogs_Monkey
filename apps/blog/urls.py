from django.urls import path
from . import views

app_name = 'blog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('explore/', views.BlogListView.as_view(), name='blog_list'),
    path('post/<slug:slug>/', views.BlogDetailView.as_view(), name='blog_detail'),
    path('category/<slug:slug>/', views.CategoryDetailView.as_view(), name='category_detail'),
    path('tag/<slug:slug>/', views.TagDetailView.as_view(), name='tag_detail'),
    path('author/<str:username>/', views.AuthorProfileView.as_view(), name='author_profile'),
    path('post/<int:blog_id>/like/', views.ToggleLikeView.as_view(), name='toggle_like'),
    path('post/<int:blog_id>/bookmark/', views.ToggleBookmarkView.as_view(), name='toggle_bookmark'),
    path('post/<int:blog_id>/comment/', views.AddCommentView.as_view(), name='add_comment'),
]
