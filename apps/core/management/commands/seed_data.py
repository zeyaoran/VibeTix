from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Artist, Venue, Event
from apps.tickets.models import TicketCategory


class Command(BaseCommand):
    help = "Seeds test users and sample concert data for VibeTix Foundation Phase"

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("Seeding VibeTix initial data..."))

        # 1. Admin Superuser
        admin_user, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@vibetix.com',
                'first_name': 'Super',
                'last_name': 'Admin',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'is_verified': True,
            }
        )
        if created:
            admin_user.set_password('admin123')
            admin_user.save()
            self.stdout.write(self.style.SUCCESS("Created Superuser: admin (pass: admin123)"))
        else:
            self.stdout.write("Superuser 'admin' already exists.")

        # 2. Promoter / Organizer
        organizer_user, created = User.objects.get_or_create(
            username='organizer',
            defaults={
                'email': 'promoter@vibetix.com',
                'first_name': 'LiveNation',
                'last_name': 'Promoter',
                'role': User.Role.ORGANIZER,
                'is_staff': True,
                'is_verified': True,
            }
        )
        if created:
            organizer_user.set_password('organizer123')
            organizer_user.save()
            self.stdout.write(self.style.SUCCESS("Created Organizer: organizer (pass: organizer123)"))

        # 3. Customer User
        customer_user, created = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@vibetix.com',
                'first_name': 'Alex',
                'last_name': 'MusicFan',
                'role': User.Role.CUSTOMER,
                'is_verified': True,
            }
        )
        if created:
            customer_user.set_password('customer123')
            customer_user.save()
            self.stdout.write(self.style.SUCCESS("Created Customer: customer (pass: customer123)"))

        # 4. Venues
        venue_gbk, _ = Venue.objects.get_or_create(
            name='Gelora Bung Karno Main Stadium',
            defaults={
                'address': 'Jl. Pintu Satu Senayan, Gelora, Kecamatan Tanah Abang',
                'city': 'Jakarta Pusat',
                'province': 'DKI Jakarta',
                'postal_code': '10270',
                'capacity': 77000,
                'latitude': -6.218576,
                'longitude': 106.801783,
            }
        )

        venue_ice, _ = Venue.objects.get_or_create(
            name='Indonesia Convention Exhibition (ICE BSD)',
            defaults={
                'address': 'Jl. BSD Grand Boulevard No.1, Pagedangan',
                'city': 'Tangerang',
                'province': 'Banten',
                'postal_code': '15339',
                'capacity': 18000,
                'latitude': -6.300584,
                'longitude': 106.637500,
            }
        )

        # 5. Artists
        artist_coldplay, _ = Artist.objects.get_or_create(
            name='Coldplay',
            defaults={
                'bio': 'British rock band formed in London in 1997. Known for global hits like Yellow, Fix You, and Viva La Vida.',
                'genre': 'Alternative Rock / Pop',
                'instagram_handle': 'coldplay',
                'spotify_url': 'https://open.spotify.com/artist/4gzpq5YKM9GDflWwAjHTEZ',
            }
        )

        artist_bruno, _ = Artist.objects.get_or_create(
            name='Bruno Mars',
            defaults={
                'bio': 'Grammy award-winning American singer, songwriter, and record producer renowned for energetic stage performances.',
                'genre': 'Pop / Funk / R&B',
                'instagram_handle': 'brunomars',
                'spotify_url': 'https://open.spotify.com/artist/0du5cEVh5yTK9QJze8zA0C',
            }
        )

        # 6. Events
        now = timezone.now()
        event_1, created = Event.objects.get_or_create(
            title='Coldplay: Music of the Spheres World Tour Jakarta',
            defaults={
                'description': 'The world-renowned British rock band Coldplay returns to Jakarta for a massive stadium tour featuring sustainable energy initiatives, LED wristbands, and timeless hits.',
                'venue': venue_gbk,
                'start_time': now + timedelta(days=45, hours=19),
                'end_time': now + timedelta(days=45, hours=23),
                'doors_open': now + timedelta(days=45, hours=16),
                'status': Event.Status.ON_SALE,
                'age_restriction': 'All Ages (Under 14 with guardian)',
                'video_url': 'https://www.youtube.com/watch?v=k4V3Ui68k7U',
                'terms_conditions': '1. ID matching ticket name required. 2. Non-refundable. 3. Wristband exchange details will be emailed.',
                'is_featured': True,
            }
        )
        if created:
            event_1.artists.add(artist_coldplay)

            # Ticket categories for Event 1 (Category-based ticketing only, no individual seats)
            TicketCategory.objects.create(
                event=event_1,
                name='VIP Ultimate Experience',
                description='Special backstage tour, exclusive merchandise, early access, dedicated VIP entrance.',
                price=11000000,
                total_quota=300,
                available_quota=300,
                max_per_order=2,
                sales_start_time=now - timedelta(days=5),
                sales_end_time=now + timedelta(days=40),
                is_active=True,
            )
            TicketCategory.objects.create(
                event=event_1,
                name='CAT 1 (Numbered Seating Zone)',
                description='Front central tier tiered arena seating with clear panoramic view.',
                price=5000000,
                total_quota=1500,
                available_quota=1500,
                max_per_order=4,
                sales_start_time=now - timedelta(days=5),
                sales_end_time=now + timedelta(days=40),
                is_active=True,
            )
            TicketCategory.objects.create(
                event=event_1,
                name='Festival (Standing Field Zone)',
                description='Main arena pitch standing access closest to the extended B-stage.',
                price=3500000,
                total_quota=5000,
                available_quota=5000,
                max_per_order=4,
                sales_start_time=now - timedelta(days=5),
                sales_end_time=now + timedelta(days=40),
                is_active=True,
            )
            TicketCategory.objects.create(
                event=event_1,
                name='CAT 2 (Upper Tier)',
                description='Upper bowl seating zone with great stage lighting angles.',
                price=2500000,
                total_quota=3000,
                available_quota=3000,
                max_per_order=4,
                sales_start_time=now - timedelta(days=5),
                sales_end_time=now + timedelta(days=40),
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("Created Event: Coldplay World Tour with 4 Ticket Categories"))

        # Event 2
        event_2, created = Event.objects.get_or_create(
            title='Bruno Mars Live in Jakarta 2026',
            defaults={
                'description': 'Live performance by the 15-time Grammy Award winner Bruno Mars featuring chart-topping anthems.',
                'venue': venue_ice,
                'start_time': now + timedelta(days=60, hours=20),
                'end_time': now + timedelta(days=60, hours=22, minutes=30),
                'doors_open': now + timedelta(days=60, hours=17),
                'status': Event.Status.PUBLISHED,
                'age_restriction': '12+',
                'video_url': 'https://www.youtube.com/watch?v=PMivT7MJ41M',
                'terms_conditions': 'Standard concert ticketing terms apply.',
                'is_featured': True,
            }
        )
        if created:
            event_2.artists.add(artist_bruno)
            TicketCategory.objects.create(
                event=event_2,
                name='VIP Gold Package',
                description='Premium center seating + VIP lounge access & commemorative lanyard.',
                price=7500000,
                total_quota=200,
                available_quota=200,
                max_per_order=2,
                sales_start_time=now + timedelta(days=1),
                sales_end_time=now + timedelta(days=55),
                is_active=True,
            )
            TicketCategory.objects.create(
                event=event_2,
                name='Festival A (Standing)',
                description='Floor standing area directly in front of stage.',
                price=3000000,
                total_quota=2500,
                available_quota=2500,
                max_per_order=4,
                sales_start_time=now + timedelta(days=1),
                sales_end_time=now + timedelta(days=55),
                is_active=True,
            )
            self.stdout.write(self.style.SUCCESS("Created Event: Bruno Mars Live with Ticket Categories"))

        self.stdout.write(self.style.SUCCESS("Seeding complete!"))
