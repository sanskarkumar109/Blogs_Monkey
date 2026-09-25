import io
from PIL import Image
from django.test import TestCase
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from accounts.models import User, UserRole
from blog.models import Blog, BlogStatus, Category, Tag

def create_test_image(filename="test.jpg", content_type="image/jpeg"):
    file_bytes = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='blue')
    image.save(file_bytes, format='JPEG')
    file_bytes.seek(0)
    return SimpleUploadedFile(filename, file_bytes.read(), content_type=content_type)


class BlogEngineAndWorkflowTests(TestCase):
    def setUp(self):
        self.author1 = User.objects.create_user(username='author1', email='author1@example.com', password='Password123!', role=UserRole.AUTHOR)
        self.author2 = User.objects.create_user(username='author2', email='author2@example.com', password='Password123!', role=UserRole.AUTHOR)
        self.admin = User.objects.create_superuser(username='adminuser', email='admin@example.com', password='Password123!', role=UserRole.ADMIN)

        self.category = Category.objects.create(name='Technology', icon_name='code')
        self.tag = Tag.objects.create(name='Django')

        self.blog = Blog.objects.create(
            title='Mastering Scalable Applications',
            excerpt='Learn to scale Django apps effectively.',
            content='<p>Full content body text for testing...</p>',
            author=self.author1,
            category=self.category,
            status=BlogStatus.PUBLISHED
        )
        self.blog.tags.add(self.tag)

    def test_slug_and_reading_time_auto_generation(self):
        self.assertEqual(self.blog.slug, 'mastering-scalable-applications')
        self.assertGreaterEqual(self.blog.reading_time_minutes, 1)

    def test_user_create_blog_draft(self):
        self.client.login(username='author1', password='Password123!')
        response = self.client.post(reverse('dashboard:blog_create'), {
            'title': 'New Draft Article',
            'excerpt': 'Draft summary text',
            'content': '<p>Draft body</p>',
            'action': 'draft'
        })
        self.assertEqual(response.status_code, 302)
        new_blog = Blog.objects.get(title='New Draft Article')
        self.assertEqual(new_blog.status, BlogStatus.DRAFT)
        self.assertEqual(new_blog.author, self.author1)

    def test_user_submit_draft_for_review(self):
        draft_blog = Blog.objects.create(
            title='Unpublished Draft',
            excerpt='Summary',
            content='Content body',
            author=self.author1,
            status=BlogStatus.DRAFT
        )
        self.client.login(username='author1', password='Password123!')
        response = self.client.post(reverse('dashboard:blog_submit', kwargs={'pk': draft_blog.id}))
        self.assertEqual(response.status_code, 302)
        draft_blog.refresh_from_db()
        self.assertEqual(draft_blog.status, BlogStatus.PENDING_REVIEW)

    def test_ownership_protection_edit_other_user_blog_denied(self):
        self.client.login(username='author2', password='Password123!')
        response = self.client.get(reverse('dashboard:blog_edit', kwargs={'pk': self.blog.id}))
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_ownership_protection_delete_other_user_blog_denied(self):
        self.client.login(username='author2', password='Password123!')
        response = self.client.post(reverse('dashboard:blog_delete', kwargs={'pk': self.blog.id}))
        self.assertEqual(response.status_code, 403) # PermissionDenied

    def test_regular_user_cannot_approve_or_reject_blogs(self):
        pending_blog = Blog.objects.create(
            title='Pending Blog',
            excerpt='Excerpt',
            content='Body',
            author=self.author1,
            status=BlogStatus.PENDING_REVIEW
        )
        self.client.login(username='author1', password='Password123!')
        
        response_approve = self.client.post(reverse('dashboard:admin_blog_approve', kwargs={'pk': pending_blog.id}))
        self.assertEqual(response_approve.status_code, 302)
        self.assertIn('/dashboard/', response_approve.url) # Access denied redirect

        pending_blog.refresh_from_db()
        self.assertEqual(pending_blog.status, BlogStatus.PENDING_REVIEW)

    def test_admin_approve_and_publish_workflow(self):
        pending_blog = Blog.objects.create(
            title='Pending Blog Approval',
            excerpt='Excerpt',
            content='Body',
            author=self.author1,
            status=BlogStatus.PENDING_REVIEW
        )
        self.client.login(username='adminuser', password='Password123!')
        response = self.client.post(reverse('dashboard:admin_blog_approve', kwargs={'pk': pending_blog.id}))
        self.assertEqual(response.status_code, 302)
        
        pending_blog.refresh_from_db()
        self.assertEqual(pending_blog.status, BlogStatus.PUBLISHED)
        self.assertIsNotNone(pending_blog.published_at)

    def test_admin_reject_workflow_with_reason(self):
        pending_blog = Blog.objects.create(
            title='Pending Blog Rejection',
            excerpt='Excerpt',
            content='Body',
            author=self.author1,
            status=BlogStatus.PENDING_REVIEW
        )
        self.client.login(username='adminuser', password='Password123!')
        response = self.client.post(reverse('dashboard:admin_blog_reject', kwargs={'pk': pending_blog.id}), {
            'rejection_reason': 'Article requires further technical references.'
        })
        self.assertEqual(response.status_code, 302)
        
        pending_blog.refresh_from_db()
        self.assertEqual(pending_blog.status, BlogStatus.REJECTED)
        self.assertEqual(pending_blog.rejection_reason, 'Article requires further technical references.')

    def test_admin_status_transitions_unpublish_and_archive(self):
        self.client.login(username='adminuser', password='Password123!')
        
        # Unpublish to Draft
        self.client.post(reverse('dashboard:admin_blog_status', kwargs={'pk': self.blog.id}), {'status': 'draft'})
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.status, BlogStatus.DRAFT)

        # Archive
        self.client.post(reverse('dashboard:admin_blog_status', kwargs={'pk': self.blog.id}), {'status': 'archived'})
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.status, BlogStatus.ARCHIVED)

    def test_admin_toggle_featured_and_trending(self):
        self.client.login(username='adminuser', password='Password123!')
        
        self.client.post(reverse('dashboard:admin_blog_toggle_feature', kwargs={'pk': self.blog.id}))
        self.blog.refresh_from_db()
        self.assertTrue(self.blog.is_featured)

        self.client.post(reverse('dashboard:admin_blog_toggle_trending', kwargs={'pk': self.blog.id}))
        self.blog.refresh_from_db()
        self.assertTrue(self.blog.is_trending)

    def test_image_upload_validation_valid_image(self):
        self.client.login(username='author1', password='Password123!')
        valid_img = create_test_image()
        response = self.client.post(reverse('dashboard:blog_create'), {
            'title': 'Post with Image',
            'excerpt': 'Excerpt text',
            'content': 'Body content',
            'featured_image': valid_img,
            'action': 'draft'
        })
        self.assertEqual(response.status_code, 302)
        created = Blog.objects.get(title='Post with Image')
        self.assertTrue(bool(created.featured_image))

    def test_image_upload_validation_invalid_filetype(self):
        self.client.login(username='author1', password='Password123!')
        invalid_file = SimpleUploadedFile("script.sh", b"echo 'hello'", content_type="text/x-sh")
        response = self.client.post(reverse('dashboard:blog_create'), {
            'title': 'Post with Invalid File',
            'excerpt': 'Excerpt text',
            'content': 'Body content',
            'featured_image': invalid_file,
            'action': 'draft'
        })
        self.assertEqual(response.status_code, 200) # Form invalid re-render
        self.assertFalse(Blog.objects.filter(title='Post with Invalid File').exists())

    def test_view_counter_increment_on_detail_page(self):
        initial_views = self.blog.view_count
        response = self.client.get(reverse('blog:blog_detail', kwargs={'slug': self.blog.slug}))
        self.assertEqual(response.status_code, 200)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.view_count, initial_views + 1)

    def test_toggle_like_and_bookmark_views(self):
        self.client.login(username='author1', password='Password123!')
        
        # Test Toggle Like
        like_url = reverse('blog:toggle_like', kwargs={'blog_id': self.blog.id})
        response = self.client.post(like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['liked'])
        self.assertEqual(response.json()['count'], 1)

        # Toggle off
        response = self.client.post(like_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertFalse(response.json()['liked'])
        self.assertEqual(response.json()['count'], 0)

        # Test Toggle Bookmark
        bm_url = reverse('blog:toggle_bookmark', kwargs={'blog_id': self.blog.id})
        response = self.client.post(bm_url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['bookmarked'])

    def test_user_likes_and_bookmarks_views(self):
        self.client.login(username='author1', password='Password123!')
        
        # Like & Bookmark article
        self.client.post(reverse('blog:toggle_like', kwargs={'blog_id': self.blog.id}))
        self.client.post(reverse('blog:toggle_bookmark', kwargs={'blog_id': self.blog.id}))

        # Test Likes View
        response = self.client.get(reverse('dashboard:likes'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.blog.title, response.content.decode('utf-8'))

        # Test Bookmarks View
        response = self.client.get(reverse('dashboard:bookmarks'))
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.blog.title, response.content.decode('utf-8'))

    def test_archive_article_view(self):
        self.client.login(username='author1', password='Password123!')
        archive_url = reverse('dashboard:blog_archive', kwargs={'pk': self.blog.id})
        
        # Archive post
        response = self.client.post(archive_url)
        self.assertEqual(response.status_code, 302)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.status, BlogStatus.ARCHIVED)

        # Unarchive post
        response = self.client.post(archive_url)
        self.assertEqual(response.status_code, 302)
        self.blog.refresh_from_db()
        self.assertEqual(self.blog.status, BlogStatus.DRAFT)


class SmartFormatterTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='writer',
            email='writer@example.com',
            password='Password123!'
        )

    def test_heading_normalization(self):
        from content.formatter import format_article, ContentParser, HeadingNormalizer
        content = "# Main Title\n\n## Section One\n\n#### Jumped Heading\n\n## Section Two"
        parser = ContentParser(content)
        blocks = parser.parse()
        normalizer = HeadingNormalizer()
        normalized = normalizer.normalize(blocks, title="Main Title")

        levels = [b.metadata['level'] for b in normalized if b.block_type == 'heading']
        self.assertEqual(levels, [2, 2, 3, 2])
        self.assertTrue(normalized[0].metadata['anchor_id'])


    def test_code_detection_and_language_inference(self):
        from content.formatter import CodeDetector
        code_snippet = "def calculate_sum(a, b):\n    return a + b"
        detector = CodeDetector()
        lang = detector.infer_language(code_snippet)
        self.assertEqual(lang, 'python')

    def test_toc_generation(self):
        from content.formatter import format_article
        content = "## Introduction\n\nText...\n\n## Getting Started\n\nText...\n\n## Deep Dive\n\nText...\n\n## Conclusion\n\nText..."
        res = format_article(content)
        self.assertTrue(res['stats']['toc_generated'])
        self.assertIn('Table of Contents', res['formatted_html'])

    def test_callout_detection(self):
        from content.formatter import format_article
        content = "Important: Do not share secret keys in public repositories."
        res = format_article(content)
        self.assertIn('IMPORTANT', res['formatted_html'])
        self.assertIn('secret keys', res['formatted_html'])

    def test_format_article_api_endpoint(self):
        self.client.force_login(self.user)
        url = reverse('dashboard:api_format_article')
        data = {
            'content': '## Overview\n\nIntro text...\n\n## Installation\n\n```bash\npip install django\n```\n\n## Usage\n\nExample...',
            'mode': 'smart',
            'title': 'How to Install Django'
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_resp = response.json()
        self.assertIn('formatted_html', json_resp)
        self.assertEqual(json_resp['stats']['code_blocks_count'], 1)


from unittest.mock import patch

class AIFeaturesTestCase(TestCase):
    def setUp(self):
        self.author1 = User.objects.create_user(
            username='user_a',
            email='usera@example.com',
            password='Password123!',
            role=UserRole.AUTHOR
        )
        self.author2 = User.objects.create_user(
            username='user_b',
            email='userb@example.com',
            password='Password123!',
            role=UserRole.AUTHOR
        )
        self.blog = Blog.objects.create(
            title='User A Article',
            excerpt='Excerpt',
            content='Content',
            author=self.author1,
            status=BlogStatus.DRAFT
        )

    def test_ai_chat_unauthenticated_denied(self):
        url = reverse('dashboard:api_ai_chat')
        response = self.client.post(url, {'message': 'Hello'}, content_type='application/json')
        self.assertIn(response.status_code, [401, 403])

    @patch('content.services.ai_service.AIService._call_llm')
    def test_ai_chat_authenticated_success(self, mock_llm):
        mock_llm.return_value = {
            'content': 'Here are 3 unique article angles for Django security.',
            'usage': {'prompt_tokens': 50, 'completion_tokens': 30, 'total_tokens': 80},
            'model': 'openai/gpt-4o-mini',
            'error': None
        }
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_chat')
        data = {'message': 'Give me ideas for Django security.'}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        json_res = response.json()
        self.assertEqual(json_res['status'], 'success')
        self.assertIn('Django security', json_res['response'])

    @patch('content.services.ai_service.AIService._call_llm')
    def test_object_level_authorization_article_ownership(self, mock_llm):
        mock_llm.return_value = {'content': 'Response', 'usage': {}, 'error': None}
        # User B trying to access AI for User A's article
        self.client.force_login(self.author2)
        url = reverse('dashboard:api_ai_chat')
        data = {
            'message': 'Analyze this',
            'article_id': self.blog.id
        }
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error'], 'FORBIDDEN')

    @patch('content.services.ai_service.AIService._call_llm')
    def test_ai_brainstorm_endpoint(self, mock_llm):
        mock_llm.return_value = {
            'content': '{"topic": "Django", "angles": [{"title": "Angle 1", "hook": "Hook 1", "target_audience": "Devs"}]}',
            'usage': {'prompt_tokens': 40, 'completion_tokens': 20, 'total_tokens': 60},
            'error': None
        }
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_brainstorm')
        response = self.client.post(url, {'topic': 'Django'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.json())

    @patch('content.services.ai_service.AIService._call_llm')
    def test_ai_outline_endpoint(self, mock_llm):
        mock_llm.return_value = {
            'content': '{"title": "Django", "sections": [{"heading": "Intro", "level": "h2", "talking_points": ["Point 1"]}]}',
            'usage': {'prompt_tokens': 40, 'completion_tokens': 20, 'total_tokens': 60},
            'error': None
        }
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_outline')
        response = self.client.post(url, {'topic': 'Django'}, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data', response.json())

    @patch('content.services.ai_service.AIService._call_llm')
    def test_ai_selection_action_endpoint(self, mock_llm):
        mock_llm.return_value = {
            'content': 'Simplified version of selected text.',
            'usage': {'prompt_tokens': 20, 'completion_tokens': 10, 'total_tokens': 30},
            'error': None
        }
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_selection')
        data = {'text': 'Django middleware processes HTTP requests.', 'action': 'simplify'}
        response = self.client.post(url, data, content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['action'], 'simplify')

    def test_rate_limiting_enforcement(self):
        from content.services import AIRateLimiter
        user_id = self.author1.id
        # Saturate rate limit
        for _ in range(25):
            AIRateLimiter.increment(user_id, 'chat')
        
        self.assertTrue(AIRateLimiter.is_rate_limited(user_id, 'chat'))
        
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_chat')
        response = self.client.post(url, {'message': 'Hello'}, content_type='application/json')
        self.assertEqual(response.status_code, 429)

    @patch('content.services.ai_service.AIService._call_llm')
    def test_usage_tracking_record_created(self, mock_llm):
        from content.models import AIUsage
        mock_llm.return_value = {
            'content': 'Response text',
            'usage': {'prompt_tokens': 100, 'completion_tokens': 50, 'total_tokens': 150},
            'model': 'openai/gpt-4o-mini',
            'error': None
        }
        initial_count = AIUsage.objects.count()
        self.client.force_login(self.author1)
        url = reverse('dashboard:api_ai_chat')
        self.client.post(url, {'message': 'Test query'}, content_type='application/json')
        self.assertEqual(AIUsage.objects.count(), initial_count + 1)
        usage = AIUsage.objects.first()
        self.assertEqual(usage.user, self.author1)
        self.assertEqual(usage.total_tokens, 150)


