from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from blog.models import Blog, BlogStatus, Comment
from content.models import SiteSetting, Report, ReportStatus

class ContentTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='reporter', email='reporter@example.com', password='Password123!')
        self.author = User.objects.create_user(username='author', email='author@example.com', password='Password123!')
        self.blog = Blog.objects.create(
            title='Reportable Blog',
            excerpt='Excerpt',
            content='Body',
            author=self.author,
            status=BlogStatus.PUBLISHED
        )
        self.comment = Comment.objects.create(
            blog=self.blog,
            author=self.author,
            content='Inappropriate comment'
        )

    def test_health_check_endpoint(self):
        response = self.client.get(reverse('content:health_check'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'healthy')

    def test_robots_txt(self):
        response = self.client.get(reverse('content:robots_txt'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'User-agent: *')

    def test_rss_feed(self):
        response = self.client.get(reverse('content:rss_feed'))
        self.assertEqual(response.status_code, 200)

    def test_singleton_site_settings(self):
        s1 = SiteSetting.get_settings()
        s2 = SiteSetting.get_settings()
        self.assertEqual(s1.pk, s2.pk)

    def test_report_blog_creation(self):
        self.client.login(username='reporter', password='Password123!')
        response = self.client.post(reverse('content:report_blog', kwargs={'blog_id': self.blog.id}), {
            'reason': 'Contains inappropriate content.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(blog=self.blog, reported_by=self.user).exists())

    def test_report_comment_creation(self):
        self.client.login(username='reporter', password='Password123!')
        response = self.client.post(reverse('content:report_comment', kwargs={'comment_id': self.comment.id}), {
            'reason': 'Abusive language.'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Report.objects.filter(comment=self.comment, reported_by=self.user).exists())
