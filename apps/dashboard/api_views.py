from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.models import Count, Q

from blog.models import Blog, BlogStatus, Category, Tag
from accounts.models import User, UserStatus
from content.models import Report
from .serializers import BlogSerializer, CategorySerializer, TagSerializer, UserSerializer

class IsAuthorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.author == request.user or request.user.is_site_admin


class BlogViewSet(viewsets.ModelViewSet):
    serializer_class = BlogSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrAdmin]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = Blog.objects.select_related('author', 'author__profile', 'category').prefetch_related('tags')
        if self.request.user.is_authenticated and (self.request.user.is_site_admin or self.request.user.role == 'admin'):
            return queryset
        elif self.request.user.is_authenticated:
            return queryset.filter(Q(status=BlogStatus.PUBLISHED) | Q(author=self.request.user))
        return queryset.filter(status=BlogStatus.PUBLISHED)

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


class SearchAutocompleteAPIView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        query = request.GET.get('q', '').strip()
        if not query or len(query) < 2:
            return Response([], status=status.HTTP_200_OK)

        blogs = Blog.published.filter(
            Q(title__icontains=query) |
            Q(excerpt__icontains=query) |
            Q(author__username__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related('category', 'author')[:5]

        results = [
            {
                'title': b.title,
                'slug': b.slug,
                'url': b.get_absolute_url(),
                'category': b.category.name if b.category else None,
                'author': b.author.username
            }
            for b in blogs
        ]
        return Response(results, status=status.HTTP_200_OK)


class DashboardStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        stats = {
            'total_users': User.objects.count(),
            'total_blogs': Blog.objects.count(),
            'published_blogs': Blog.objects.filter(status=BlogStatus.PUBLISHED).count(),
            'pending_review': Blog.objects.filter(status=BlogStatus.PENDING_REVIEW).count(),
            'draft_blogs': Blog.objects.filter(status=BlogStatus.DRAFT).count(),
            'pending_reports': Report.objects.filter(status='pending').count(),
            'total_views': sum(b.view_count for b in Blog.objects.all())
        }
        return Response(stats, status=status.HTTP_200_OK)


class FormatArticleAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from content.formatter import format_article
        from content.services import AIRateLimiter

        if AIRateLimiter.is_rate_limited(request.user.id, 'format'):
            return Response(
                {'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI formatting rate limit exceeded. Please wait a moment before trying again.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        AIRateLimiter.increment(request.user.id, 'format')

        raw_content = request.data.get('content', '')
        mode = request.data.get('mode', 'smart')
        title = request.data.get('title', '')
        seo_title = request.data.get('seo_title', '')
        seo_desc = request.data.get('seo_description', '')

        result = format_article(
            content=raw_content,
            mode=mode,
            title=title,
            seo_title=seo_title,
            seo_desc=seo_desc,
            user=request.user
        )

        return Response(result, status=status.HTTP_200_OK)


class AIChatAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from content.services import AIService, AIRateLimiter

        if AIRateLimiter.is_rate_limited(request.user.id, 'chat'):
            return Response(
                {'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI rate limit exceeded. Please wait 60 seconds before sending another message.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        AIRateLimiter.increment(request.user.id, 'chat')

        # Object-level authorization check for optional article_id
        article_id = request.data.get('article_id')
        if article_id:
            try:
                blog = Blog.objects.get(pk=article_id)
                if blog.author != request.user and not request.user.is_site_admin:
                    return Response({'error': 'FORBIDDEN', 'message': 'You do not have permission to access AI for this article.'}, status=status.HTTP_403_FORBIDDEN)
            except Blog.DoesNotExist:
                return Response({'error': 'NOT_FOUND', 'message': 'Article not found.'}, status=status.HTTP_404_NOT_FOUND)

        user_message = request.data.get('message', '').strip()
        if not user_message:
            return Response({'error': 'EMPTY_MESSAGE', 'message': 'Message cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        history = request.data.get('history', [])
        context = request.data.get('context', {})

        ai_service = AIService()
        result = ai_service.chat(user_message=user_message, history=history, context=context, user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class AIBrainstormAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from content.services import AIService, AIRateLimiter

        if AIRateLimiter.is_rate_limited(request.user.id, 'brainstorm'):
            return Response(
                {'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI rate limit exceeded.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        AIRateLimiter.increment(request.user.id, 'brainstorm')

        topic = request.data.get('topic', '').strip()
        if not topic:
            return Response({'error': 'EMPTY_TOPIC', 'message': 'Topic is required.'}, status=status.HTTP_400_BAD_REQUEST)

        context = request.data.get('context', {})
        ai_service = AIService()
        result = ai_service.brainstorm(topic=topic, context=context, user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class AIOutlineAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from content.services import AIService, AIRateLimiter

        if AIRateLimiter.is_rate_limited(request.user.id, 'outline'):
            return Response(
                {'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI rate limit exceeded.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        AIRateLimiter.increment(request.user.id, 'outline')

        topic = request.data.get('topic', '').strip()
        if not topic:
            return Response({'error': 'EMPTY_TOPIC', 'message': 'Topic is required.'}, status=status.HTTP_400_BAD_REQUEST)

        article_type = request.data.get('article_type', 'general')
        context = request.data.get('context', {})

        ai_service = AIService()
        result = ai_service.generate_outline(topic=topic, article_type=article_type, context=context, user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class AISelectionActionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        from content.services import AIService, AIRateLimiter

        if AIRateLimiter.is_rate_limited(request.user.id, 'selection'):
            return Response(
                {'error': 'RATE_LIMIT_EXCEEDED', 'message': 'AI rate limit exceeded.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
        AIRateLimiter.increment(request.user.id, 'selection')

        text = request.data.get('text', '').strip()
        action = request.data.get('action', 'improve').strip()
        if not text:
            return Response({'error': 'EMPTY_TEXT', 'message': 'Selected text is required.'}, status=status.HTTP_400_BAD_REQUEST)

        context = request.data.get('context', {})
        ai_service = AIService()
        result = ai_service.suggest_improvements(text=text, action=action, context=context, user=request.user)
        return Response(result, status=status.HTTP_200_OK)


class AIUsageStatsAPIView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        from content.models import AIUsage

        total_requests = AIUsage.objects.count()
        total_tokens = sum(u.total_tokens for u in AIUsage.objects.all())
        total_cost = float(sum(u.approx_cost for u in AIUsage.objects.all()))

        recent_usage = AIUsage.objects.select_related('user').values(
            'id', 'user__username', 'feature', 'model', 'total_tokens', 'approx_cost', 'status', 'created_at'
        )[:20]

        return Response({
            'total_requests': total_requests,
            'total_tokens': total_tokens,
            'total_cost_usd': round(total_cost, 4),
            'recent_usage': list(recent_usage)
        }, status=status.HTTP_200_OK)


