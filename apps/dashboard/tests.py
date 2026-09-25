from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import User, UserRole
from blog.models import Blog, BlogStatus

class DashboardAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='author', email='author@example.com', password='Password123!')
        self.admin = User.objects.create_superuser(username='admin', email='admin@example.com', password='Password123!', role=UserRole.ADMIN)
        self.blog = Blog.objects.create(
            title='API Test Article',
            excerpt='Excerpt',
            content='Content',
            author=self.user,
            status=BlogStatus.PUBLISHED
        )

    def test_get_published_blogs_api(self):
        url = reverse('dashboard:api_blog-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_jwt_auth_token_obtain(self):
        url = reverse('dashboard:token_obtain_pair')
        response = self.client.post(url, {
            'username': 'author',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_search_autocomplete_api(self):
        url = reverse('dashboard:api_search_autocomplete') + '?q=API'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], 'API Test Article')

    def test_admin_stats_api_unauthorized_for_regular_user(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('dashboard:api_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_stats_api_authorized_for_admin(self):
        self.client.force_authenticate(user=self.admin)
        url = reverse('dashboard:api_stats')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_blogs', response.data)
