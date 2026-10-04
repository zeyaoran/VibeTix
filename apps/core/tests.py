from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
from apps.accounts.models import User
from apps.events.models import Artist, Venue, Event
from apps.tickets.models import TicketCategory, Ticket
from apps.orders.models import Order, OrderItem
from apps.notifications.models import Notification
from apps.core.models import Wishlist


class VibeTixFullstackTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testcustomer',
            email='testcustomer@vibetix.com',
            password='password123',
            role=User.Role.CUSTOMER
        )
        self.artist = Artist.objects.create(
            name='Test Band',
            genre='Alternative Rock',
            bio='Test Bio'
        )
        self.venue = Venue.objects.create(
            name='Test Arena',
            address='Test Address',
            city='Jakarta Pusat',
            capacity=10000
        )
        now = timezone.now()
        self.event = Event.objects.create(
            title='Test Concert 2026',
            slug='test-concert-2026',
            description='Concert description test',
            venue=self.venue,
            start_time=now + timedelta(days=10),
            end_time=now + timedelta(days=10, hours=3),
            status=Event.Status.ON_SALE,
            is_featured=True,
            video_url='https://www.youtube.com/watch?v=k4V3Mo61fJM'
        )
        self.event.artists.add(self.artist)

        self.cat = TicketCategory.objects.create(
            event=self.event,
            name='VIP Test',
            price=Decimal('1000000'),
            total_quota=100,
            available_quota=100,
            max_per_order=4,
            sales_start_time=now - timedelta(days=1),
            sales_end_time=now + timedelta(days=10)
        )

        self.order = Order.objects.create(
            user=self.user,
            status=Order.Status.PAID,
            total_amount=Decimal('2000000'),
            admin_fee=Decimal('25000'),
            tax_amount=Decimal('200000'),
            grand_total=Decimal('2225000')
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            ticket_category=self.cat,
            quantity=2,
            unit_price=self.cat.price,
            subtotal=Decimal('2000000')
        )
        self.ticket = Ticket.objects.create(
            order_item=self.order_item,
            category=self.cat,
            holder_name='Test Customer'
        )
        self.notification = Notification.objects.create(
            user=self.user,
            title='Test Notification',
            message='Your test ticket has been issued',
            notification_type=Notification.NotificationType.ORDER,
            is_read=False
        )

    def test_homepage(self):
        response = self.client.get(reverse('core:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Concert 2026')
        self.assertContains(response, 'VIBETIX')

    def test_events_list(self):
        response = self.client.get(reverse('events:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Concert 2026')

        # Test filter
        response_filtered = self.client.get(reverse('events:list') + '?city=Jakarta+Pusat')
        self.assertEqual(response_filtered.status_code, 200)
        self.assertContains(response_filtered, 'Test Concert 2026')

        response_nomatch = self.client.get(reverse('events:list') + '?city=Nonexistent')
        self.assertEqual(response_nomatch.status_code, 200)
        self.assertContains(response_nomatch, 'No Events Found')

    def test_event_detail(self):
        response = self.client.get(reverse('events:detail', kwargs={'slug': self.event.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Concert 2026')
        self.assertContains(response, 'VIP Test')
        self.assertContains(response, 'https://www.youtube.com/embed/k4V3Mo61fJM')

    def test_artists_pages(self):
        response = self.client.get(reverse('events:artist_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Band')

        response_detail = self.client.get(reverse('events:artist_detail', kwargs={'slug': self.artist.slug}))
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, 'Test Band')
        self.assertContains(response_detail, 'Test Concert 2026')

    def test_venues_pages(self):
        response = self.client.get(reverse('events:venue_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Arena')

        response_detail = self.client.get(reverse('events:venue_detail', kwargs={'slug': self.venue.slug}))
        self.assertEqual(response_detail.status_code, 200)
        self.assertContains(response_detail, 'Test Arena')
        self.assertContains(response_detail, 'Test Concert 2026')

    def test_calendar_page(self):
        response = self.client.get(reverse('core:calendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tour Date Calendar')

    def test_wishlist_unauthenticated_redirect(self):
        response = self.client.get(reverse('core:wishlist'))
        self.assertEqual(response.status_code, 302)

    def test_wishlist_authenticated_toggle(self):
        self.client.login(username='testcustomer', password='password123')
        
        # Toggle add to wishlist (AJAX)
        response = self.client.post(
            reverse('core:wishlist_toggle', kwargs={'event_id': self.event.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertTrue(json_data['is_wishlisted'])
        self.assertEqual(json_data['wishlist_count'], 1)

        # View wishlist
        response_view = self.client.get(reverse('core:wishlist'))
        self.assertEqual(response_view.status_code, 200)
        self.assertContains(response_view, 'Test Concert 2026')

        # Toggle remove from wishlist
        response_remove = self.client.post(
            reverse('core:wishlist_toggle', kwargs={'event_id': self.event.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response_remove.status_code, 200)
        self.assertFalse(response_remove.json()['is_wishlisted'])

    def test_notifications(self):
        self.client.login(username='testcustomer', password='password123')
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Notification')

        # Mark as read
        response_read = self.client.post(
            reverse('notifications:mark_read', kwargs={'notification_id': self.notification.id}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response_read.status_code, 200)
        self.notification.refresh_from_db()
        self.assertTrue(self.notification.is_read)

    def test_my_tickets_and_orders(self):
        self.client.login(username='testcustomer', password='password123')
        
        # My Tickets
        response_tix = self.client.get(reverse('tickets:my_tickets'))
        self.assertEqual(response_tix.status_code, 200)
        self.assertContains(response_tix, self.ticket.ticket_code)

        # Ticket Detail
        response_tix_detail = self.client.get(reverse('tickets:detail', kwargs={'ticket_code': self.ticket.ticket_code}))
        self.assertEqual(response_tix_detail.status_code, 200)
        self.assertContains(response_tix_detail, self.ticket.ticket_code)

        # Orders List
        response_orders = self.client.get(reverse('orders:list'))
        self.assertEqual(response_orders.status_code, 200)
        self.assertContains(response_orders, self.order.order_number)

        # Order Detail
        response_order_detail = self.client.get(reverse('orders:detail', kwargs={'order_number': self.order.order_number}))
        self.assertEqual(response_order_detail.status_code, 200)
        self.assertContains(response_order_detail, self.order.order_number)
