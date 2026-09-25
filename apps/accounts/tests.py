from django.test import TestCase
from django.urls import reverse
from django.core import mail
from accounts.models import User, UserRole, UserStatus

class AccountAuthenticationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testwriter',
            email='testwriter@example.com',
            password='Password123!',
            role=UserRole.AUTHOR
        )
        self.admin = User.objects.create_superuser(
            username='adminuser',
            email='admin@example.com',
            password='Password123!',
            role=UserRole.ADMIN
        )

    def test_user_registration_success(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'Password123!',
            'password2': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newuser').exists())

    def test_user_registration_invalid_password_mismatch(self):
        response = self.client.post(reverse('accounts:register'), {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password1': 'Password123!',
            'password2': 'DifferentPassword!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='mismatchuser').exists())

    def test_login_with_username(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testwriter',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testwriter@example.com',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 302)

    def test_suspended_user_login_denied(self):
        self.user.status = UserStatus.SUSPENDED
        self.user.save()
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testwriter',
            'password': 'Password123!',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "suspended")

    def test_logout(self):
        self.client.login(username='testwriter', password='Password123!')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_password_reset_email_sent(self):
        response = self.client.post(reverse('accounts:password_reset'), {
            'email': 'testwriter@example.com',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)


class AccountAuthorizationTests(TestCase):
    def setUp(self):
        self.author = User.objects.create_user(
            username='regularauthor',
            email='author@example.com',
            password='Password123!',
            role=UserRole.AUTHOR
        )
        self.admin = User.objects.create_superuser(
            username='siteadmin',
            email='admin@example.com',
            password='Password123!',
            role=UserRole.ADMIN
        )

    def test_unauthenticated_user_dashboard_redirect(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.login(username='regularauthor', password='Password123!')
        response = self.client.get(reverse('dashboard:admin_home'))
        self.assertEqual(response.status_code, 302) # Redirected with error message
        self.assertIn('/dashboard/', response.url)

    def test_admin_user_can_access_admin_dashboard(self):
        self.client.login(username='siteadmin', password='Password123!')
        response = self.client.get(reverse('dashboard:admin_home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Operational Admin Portal")
