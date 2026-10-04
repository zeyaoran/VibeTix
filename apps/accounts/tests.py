from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User


class AccountsAuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='testuser@vibetix.com',
            password='testpassword123',
            role=User.Role.CUSTOMER
        )

    def test_user_creation_and_roles(self):
        self.assertEqual(self.user.role, User.Role.CUSTOMER)
        self.assertTrue(self.user.is_customer_role)
        self.assertFalse(self.user.is_admin_role)

    def test_login_view_get(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser',
            'password': 'testpassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_login_with_email(self):
        response = self.client.post(reverse('accounts:login'), {
            'username': 'testuser@vibetix.com',
            'password': 'testpassword123'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_register_view(self):
        response = self.client.post(reverse('accounts:register'), {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'username': 'janedoe',
            'email': 'jane@vibetix.com',
            'phone_number': '08123456789',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.filter(username='janedoe').exists())
        new_user = User.objects.get(username='janedoe')
        self.assertEqual(new_user.role, User.Role.CUSTOMER)

    def test_logout_view(self):
        self.client.login(username='testuser', password='testpassword123')
        response = self.client.get(reverse('accounts:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context['user'].is_authenticated)
