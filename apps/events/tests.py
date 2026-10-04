from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from apps.events.models import Artist, Venue, Event
from apps.tickets.models import TicketCategory


class EventModelTests(TestCase):
    def setUp(self):
        self.venue = Venue.objects.create(
            name='Test Arena',
            address='123 Music Blvd',
            city='Jakarta',
            capacity=10000
        )
        self.artist = Artist.objects.create(
            name='Test Band',
            genre='Rock'
        )
        now = timezone.now()
        self.event = Event.objects.create(
            title='Epic Rock Fest',
            venue=self.venue,
            start_time=now + timedelta(days=30),
            end_time=now + timedelta(days=30, hours=4),
            status=Event.Status.PUBLISHED
        )
        self.event.artists.add(self.artist)

    def test_event_creation_and_slug(self):
        self.assertEqual(self.event.slug, 'epic-rock-fest')
        self.assertEqual(self.event.artists.count(), 1)
        self.assertEqual(self.event.venue.city, 'Jakarta')

    def test_ticket_category_creation(self):
        now = timezone.now()
        cat = TicketCategory.objects.create(
            event=self.event,
            name='VIP',
            price=2000000,
            total_quota=100,
            available_quota=100,
            sales_start_time=now,
            sales_end_time=now + timedelta(days=29)
        )
        self.assertEqual(cat.event, self.event)
        self.assertFalse(cat.is_sold_out)

    def test_event_video_url_and_embed(self):
        self.event.video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        self.event.save()
        self.assertEqual(self.event.youtube_embed_url, "https://www.youtube.com/embed/dQw4w9WgXcQ")

