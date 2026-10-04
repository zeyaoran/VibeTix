from decimal import Decimal
from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Event, Venue, Artist
from apps.tickets.models import TicketCategory, Ticket
from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.orders.services import (
    calculate_order_totals,
    validate_ticket_category_for_purchase,
    create_order_from_cart,
    mark_order_as_paid,
    ADMIN_FEE,
    TAX_RATE,
)
from apps.payments.models import Payment


class Phase3TransactionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = User.objects.create_user(
            username='testcustomer',
            email='customer@vibetix.com',
            password='Password123!',
            role=User.Role.CUSTOMER,
            first_name='John',
            last_name='Doe',
            phone_number='+6281234567890'
        )
        self.other_customer = User.objects.create_user(
            username='othercustomer',
            email='other@vibetix.com',
            password='Password123!',
            role=User.Role.CUSTOMER
        )
        self.admin_user = User.objects.create_superuser(
            username='adminuser',
            email='admin@vibetix.com',
            password='Password123!',
            role=User.Role.ADMIN,
            is_staff=True,
            is_superuser=True
        )

        self.venue = Venue.objects.create(
            name='Jakarta International Stadium',
            address='Tanjung Priok',
            city='Jakarta',
            capacity=82000
        )

        now = timezone.now()
        self.event = Event.objects.create(
            title='Cosmic Echoes World Tour',
            description='Spectacular stadium concert tour.',
            venue=self.venue,
            start_time=now + timedelta(days=30),
            end_time=now + timedelta(days=30, hours=4),
            doors_open=now + timedelta(days=30, hours=-2),
            status=Event.Status.ON_SALE,
            is_featured=True
        )

        self.vip_category = TicketCategory.objects.create(
            event=self.event,
            name='VIP Floor',
            description='Front row access and merchandise pack',
            price=Decimal('2500000.00'),
            total_quota=100,
            available_quota=100,
            max_per_order=4,
            sales_start_time=now - timedelta(days=5),
            sales_end_time=now + timedelta(days=25),
            is_active=True
        )

        self.cat1_category = TicketCategory.objects.create(
            event=self.event,
            name='CAT 1 Tribune',
            description='Numbered seated tribune area',
            price=Decimal('1500000.00'),
            total_quota=500,
            available_quota=500,
            max_per_order=4,
            sales_start_time=now - timedelta(days=5),
            sales_end_time=now + timedelta(days=25),
            is_active=True
        )

    def test_customer_login_flow(self):
        """Customer login should authenticate and redirect to core:home, not admin."""
        response = self.client.post(reverse('accounts:login'), {
            'username': 'customer@vibetix.com',
            'password': 'Password123!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('core:home'))

        # Check that customer cannot access admin dashboard
        admin_resp = self.client.get('/admin/')
        # Django admin redirects non-staff users to admin login
        self.assertEqual(admin_resp.status_code, 302)

    def test_cart_add_and_calculations(self):
        """Customer can add tickets to cart and calculated financials are accurate."""
        self.client.login(username='testcustomer', password='Password123!')

        # Add 2 VIP tickets
        response = self.client.post(reverse('orders:cart_add', kwargs={'category_id': self.vip_category.id}), {
            'quantity': 2
        })
        self.assertEqual(response.status_code, 302)

        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.total_items, 2)
        self.assertEqual(cart.subtotal, Decimal('5000000.00'))

        totals = calculate_order_totals(cart.subtotal)
        self.assertEqual(totals['subtotal'], Decimal('5000000.00'))
        self.assertEqual(totals['admin_fee'], ADMIN_FEE)
        self.assertEqual(totals['tax_amount'], Decimal('500000.00'))
        self.assertEqual(totals['grand_total'], Decimal('5510000.00'))

    def test_cart_quantity_update_and_removal(self):
        """Customer can update cart item quantity and remove items."""
        self.client.login(username='testcustomer', password='Password123!')
        self.client.post(reverse('orders:cart_add', kwargs={'category_id': self.vip_category.id}), {'quantity': 2})

        cart = Cart.objects.get(user=self.customer)
        item = cart.items.first()

        # Update to 3
        self.client.post(reverse('orders:cart_update', kwargs={'item_id': item.id}), {'quantity': 3})
        item.refresh_from_db()
        self.assertEqual(item.quantity, 3)

        # Remove item
        self.client.post(reverse('orders:cart_remove', kwargs={'item_id': item.id}))
        self.assertEqual(cart.items.count(), 0)

    def test_max_per_order_validation(self):
        """Cannot exceed category max_per_order."""
        self.client.login(username='testcustomer', password='Password123!')
        # Requesting 5 tickets when max is 4
        is_valid, msg = validate_ticket_category_for_purchase(self.vip_category, 5)
        self.assertFalse(is_valid)
        self.assertIn("Maximum limit", msg)

    def test_order_creation_and_quota_reduction(self):
        """Order creation creates PENDING order and decrements category quota safely."""
        self.client.login(username='testcustomer', password='Password123!')
        self.client.post(reverse('orders:cart_add', kwargs={'category_id': self.vip_category.id}), {'quantity': 2})

        initial_quota = self.vip_category.available_quota
        response = self.client.post(reverse('orders:checkout_process'))
        self.assertEqual(response.status_code, 302)

        order = Order.objects.filter(user=self.customer).first()
        self.assertIsNotNone(order)
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(order.items.count(), 1)
        self.assertEqual(order.total_amount, Decimal('5000000.00'))
        self.assertEqual(order.grand_total, Decimal('5510000.00'))

        # Quota should be reduced
        self.vip_category.refresh_from_db()
        self.assertEqual(self.vip_category.available_quota, initial_quota - 2)

        # Cart should now be empty
        cart = Cart.objects.get(user=self.customer)
        self.assertEqual(cart.items.count(), 0)

    def test_order_ownership_protection(self):
        """User A cannot view User B's order receipt."""
        self.client.login(username='testcustomer', password='Password123!')
        self.client.post(reverse('orders:cart_add', kwargs={'category_id': self.vip_category.id}), {'quantity': 1})
        self.client.post(reverse('orders:checkout_process'))
        order = Order.objects.filter(user=self.customer).first()

        # Log in as other user
        self.client.login(username='othercustomer', password='Password123!')
        response = self.client.get(reverse('orders:detail', kwargs={'order_number': order.order_number}))
        self.assertEqual(response.status_code, 404)

    def test_payment_settlement_and_ticket_generation(self):
        """Settling payment generates authentic tickets in digital wallet."""
        self.client.login(username='testcustomer', password='Password123!')
        self.client.post(reverse('orders:cart_add', kwargs={'category_id': self.vip_category.id}), {'quantity': 2})
        self.client.post(reverse('orders:checkout_process'))
        order = Order.objects.filter(user=self.customer).first()

        # Mark order as paid
        mark_order_as_paid(order)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.PAID)
        self.assertIsNotNone(order.paid_at)

        # Verify Tickets generated
        tickets = Ticket.objects.filter(order_item__order=order)
        self.assertEqual(tickets.count(), 2)
        first_ticket = tickets.first()
        self.assertTrue(first_ticket.ticket_code.startswith('TIX-'))
        self.assertEqual(first_ticket.status, Ticket.Status.ISSUED)
        self.assertEqual(first_ticket.holder_name, 'John Doe')

        # Test My Tickets page
        ticket_response = self.client.get(reverse('tickets:my_tickets'))
        self.assertEqual(ticket_response.status_code, 200)
        self.assertContains(ticket_response, first_ticket.ticket_code)

        # Test Ticket Detail view
        detail_response = self.client.get(reverse('tickets:detail', kwargs={'ticket_code': first_ticket.ticket_code}))
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, 'VIP Floor')
