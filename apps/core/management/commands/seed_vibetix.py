from decimal import Decimal
from datetime import timedelta
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Artist, Venue, Event
from apps.tickets.models import TicketCategory, Ticket
from apps.orders.models import Order, OrderItem
from apps.notifications.models import Notification
from apps.core.models import Wishlist


class Command(BaseCommand):
    help = 'Seeds realistic concert ticketing data for VibeTix user-facing platform'

    def handle(self, *args, **options):
        self.stdout.write("Starting VibeTix realistic database seeding...")

        # 1. Users
        admin_user, _ = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@vibetix.com',
                'first_name': 'Chief',
                'last_name': 'Admin',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
            }
        )
        if not admin_user.has_usable_password():
            admin_user.set_password('admin12345')
            admin_user.save()

        organizer_user, _ = User.objects.get_or_create(
            username='organizer',
            defaults={
                'email': 'promoter@vibetix.com',
                'first_name': 'LiveNation',
                'last_name': 'ID',
                'role': User.Role.ORGANIZER,
                'is_staff': False,
            }
        )
        if not organizer_user.has_usable_password():
            organizer_user.set_password('promoter123')
            organizer_user.save()

        customer_user, _ = User.objects.get_or_create(
            username='customer',
            defaults={
                'email': 'customer@vibetix.com',
                'first_name': 'Arya',
                'last_name': 'Pratama',
                'phone_number': '+62 812-8888-9999',
                'role': User.Role.CUSTOMER,
            }
        )
        if not customer_user.has_usable_password():
            customer_user.set_password('customer123')
            customer_user.save()

        self.stdout.write(self.style.SUCCESS("[OK] Users verified: admin, organizer, customer"))

        # 2. Artists
        artists_data = [
            {
                'name': 'Coldplay',
                'genre': 'Alternative Rock / Pop',
                'bio': 'British rock band formed in London in 1997. Renowned for spectacular world tours, synchronised LED wristbands, and universally beloved anthems like "Yellow", "Fix You", and "Viva La Vida".',
                'instagram_handle': 'coldplay',
                'spotify_url': 'https://open.spotify.com/artist/4gzpq5YvW9XsIo9ipVKIUt',
            },
            {
                'name': 'Bruno Mars',
                'genre': 'Pop / Funk / R&B',
                'bio': 'Multi-Grammy Award-winning superstar celebrated for timeless showmanship, electrifying funk choreography, and smash singles including "24K Magic", "Locked Out of Heaven", and "Uptown Funk".',
                'instagram_handle': 'brunomars',
                'spotify_url': 'https://open.spotify.com/artist/0du5cEVh5yTK9QJze8zA0C',
            },
            {
                'name': 'Dua Lipa',
                'genre': 'Pop / Disco / Dance',
                'bio': 'Global pop powerhouse commanding stadiums worldwide with radical optimism, disco-pop synthesizers, and massive global hits such as "Levitating", "Don\'t Start Now", and "Houdini".',
                'instagram_handle': 'dualipa',
                'spotify_url': 'https://open.spotify.com/artist/6M2wZ9GZgrQXHCFfjv46we',
            },
            {
                'name': 'Arctic Monkeys',
                'genre': 'Indie Rock / Post-Punk',
                'bio': 'Sheffield-born indie rock royalty fronted by Alex Turner, famous for poetic lyrics, vintage guitars, and landmark albums from "Whatever People Say I Am..." to "AM".',
                'instagram_handle': 'arcticmonkeys',
                'spotify_url': 'https://open.spotify.com/artist/7Ln80taz6r0PggBa0fiz48',
            },
            {
                'name': 'NIKI',
                'genre': 'Indie Pop / R&B',
                'bio': 'Indonesian singer-songwriter and 88rising pioneer known for intimate storytelling, acoustic guitars, and chart-topping hits like "Every Summertime", "High School in Jakarta", and "Oceans & Engines".',
                'instagram_handle': 'nikizefanya',
                'spotify_url': 'https://open.spotify.com/artist/2kxP07AlicImggQYGdd6aK',
            },
            {
                'name': 'RADWIMPS',
                'genre': 'J-Rock / Alternative',
                'bio': 'Acclaimed Japanese rock band celebrated for emotive cinema soundtracks including "Your Name" and "Suzume", and energetic stadium rock performances worldwide.',
                'instagram_handle': 'radwimps_jp',
                'spotify_url': 'https://open.spotify.com/artist/1F5ti1VzPwh1988s97gQ0V',
            },
            {
                'name': 'Wave to Earth',
                'genre': 'Indie Pop / Lo-Fi / Jazz',
                'bio': 'South Korean indie band fusing dreamy lo-fi guitar tones with soothing jazz-pop sensibilities, crafting international viral sensations like "seasons" and "bad".',
                'instagram_handle': 'wave_to_earth',
                'spotify_url': 'https://open.spotify.com/artist/2jUoxNknP8gWp5l01vR0lR',
            },
            {
                'name': 'Billie Eilish',
                'genre': 'Electropop / Alt-Pop',
                'bio': 'Academy and Grammy Award winner known for boundary-pushing production, haunting vocals, and genre-defining anthems like "bad guy", "birds of a feather", and "Ocean Eyes".',
                'instagram_handle': 'billieeilish',
                'spotify_url': 'https://open.spotify.com/artist/6qqNVTkY8u39CG0ioqBeGR',
            },
        ]

        artists_map = {}
        for adata in artists_data:
            artist, _ = Artist.objects.update_or_create(
                name=adata['name'],
                defaults=adata
            )
            artists_map[artist.name] = artist

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(artists_map)} Artists synchronized"))

        # 3. Venues
        venues_data = [
            {
                'name': 'Gelora Bung Karno Main Stadium',
                'address': 'Jl. Pintu Satu Senayan, Gelora, Kecamatan Tanah Abang',
                'city': 'Jakarta Pusat',
                'province': 'DKI Jakarta',
                'postal_code': '10270',
                'capacity': 77000,
                'latitude': Decimal('-6.218500'),
                'longitude': Decimal('106.801800'),
            },
            {
                'name': 'Indonesia Convention Exhibition (ICE BSD)',
                'address': 'Jl. BSD Grand Boulevard No.1, Pagedangan',
                'city': 'Tangerang',
                'province': 'Banten',
                'postal_code': '15339',
                'capacity': 18000,
                'latitude': Decimal('-6.301500'),
                'longitude': Decimal('106.637500'),
            },
            {
                'name': 'Beach City International Stadium (BCIS)',
                'address': 'Taman Impian Jaya Ancol, Jl. Lodan Timur No.7',
                'city': 'Jakarta Utara',
                'province': 'DKI Jakarta',
                'postal_code': '14430',
                'capacity': 20000,
                'latitude': Decimal('-6.120500'),
                'longitude': Decimal('106.843000'),
            },
            {
                'name': 'Tennis Indoor Senayan',
                'address': 'Jl. Asia Afrika No.5, Gelora, Tanah Abang',
                'city': 'Jakarta Pusat',
                'province': 'DKI Jakarta',
                'postal_code': '10270',
                'capacity': 8500,
                'latitude': Decimal('-6.216000'),
                'longitude': Decimal('106.799500'),
            },
            {
                'name': 'JIExpo Kemayoran Arena',
                'address': 'Gedung Pusat Niaga Lt. 1, Arena PRJ Kemayoran',
                'city': 'Jakarta Pusat',
                'province': 'DKI Jakarta',
                'postal_code': '10620',
                'capacity': 25000,
                'latitude': Decimal('-6.148200'),
                'longitude': Decimal('106.848600'),
            },
        ]

        venues_map = {}
        for vdata in venues_data:
            venue, _ = Venue.objects.update_or_create(
                name=vdata['name'],
                defaults=vdata
            )
            venues_map[venue.name] = venue

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(venues_map)} Venues synchronized"))

        # 4. Events
        now = timezone.now()
        terms_text = """1. All ticket sales are final and non-refundable unless the event is officially cancelled.
2. Valid government-issued photo ID (KTP / Passport / Driver License) matching the ticket holder name must be presented at gate entry.
3. Category wristbands will be redeemed at designated venue booths on show day starting at 10:00 AM WIB.
4. Professional cameras, recording equipment, sharp objects, and outside food/beverages are strictly prohibited inside the arena.
5. Minors under 14 years old must be accompanied by an adult guardian holding a ticket in the same category."""

        events_data = [
            {
                'title': 'Coldplay: Music of the Spheres World Tour Jakarta',
                'slug': 'coldplay-music-of-the-spheres-world-tour-jakarta',
                'venue': venues_map['Gelora Bung Karno Main Stadium'],
                'artists': [artists_map['Coldplay']],
                'start_time': now + timedelta(days=25, hours=19),
                'end_time': now + timedelta(days=25, hours=23),
                'doors_open': now + timedelta(days=25, hours=16),
                'status': Event.Status.ON_SALE,
                'is_featured': True,
                'age_restriction': 'All Ages (Under 14 with Guardian)',
                'video_url': 'https://www.youtube.com/watch?v=k4V3Mo61fJM',
                'description': 'Coldplay returns to Jakarta for an unprecedented stadium spectacle. Featuring kinetic dance floors, solar-powered kinetic stages, and wristbands illuminating the night in synchronised color.',
                'terms_conditions': terms_text,
                'categories': [
                    ('VIP Ultimate Experience', 'Prime front-stage zone, dedicated lounge entrance, limited merchandise gift & VIP lanyard', Decimal('11000000'), 300, 48, 2),
                    ('CAT 1 (Numbered Seating)', 'Lower tier grandstand with direct center-stage elevated sightlines', Decimal('5000000'), 1500, 320, 4),
                    ('Festival (Standing Field)', 'Full immersive standing field area close to the B-stage extension', Decimal('3500000'), 5000, 1140, 4),
                    ('CAT 2 (Upper Tier Seating)', 'Elevated stadium seating with panoramic view of full LED light show', Decimal('2500000'), 3000, 680, 6),
                ]
            },
            {
                'title': 'Bruno Mars Live in Jakarta 2026',
                'slug': 'bruno-mars-live-in-jakarta-2026',
                'venue': venues_map['Indonesia Convention Exhibition (ICE BSD)'],
                'artists': [artists_map['Bruno Mars']],
                'start_time': now + timedelta(days=40, hours=20),
                'end_time': now + timedelta(days=40, hours=23),
                'doors_open': now + timedelta(days=40, hours=17),
                'status': Event.Status.ON_SALE,
                'is_featured': True,
                'age_restriction': '12+ with Photo ID',
                'video_url': 'https://www.youtube.com/watch?v=PMivT7MJ41M',
                'description': 'The unstoppable Bruno Mars brings the greatest funk & soul party in the world to Jakarta. An unforgettable night of brass horns, impeccable dancing, and timeless chart-toppers.',
                'terms_conditions': terms_text,
                'categories': [
                    ('VIP Gold Package', 'Exclusive front rows, express merchandise access & commemorative laminate', Decimal('7500000'), 250, 15, 2),
                    ('Festival A (Standing Front)', 'Standing zone directly in front of main runway', Decimal('3500000'), 3000, 420, 4),
                    ('Festival B (Standing Regular)', 'Standing field zone behind Festival A', Decimal('2450000'), 4000, 890, 4),
                    ('CAT 1 Seated Tier', 'Comfortable tiered grandstand seating', Decimal('1950000'), 2000, 310, 4),
                ]
            },
            {
                'title': 'Dua Lipa: Radical Optimism World Tour',
                'slug': 'dua-lipa-radical-optimism-tour-jakarta',
                'venue': venues_map['Beach City International Stadium (BCIS)'],
                'artists': [artists_map['Dua Lipa']],
                'start_time': now + timedelta(days=55, hours=19, minutes=30),
                'end_time': now + timedelta(days=55, hours=22, minutes=45),
                'doors_open': now + timedelta(days=55, hours=16, minutes=30),
                'status': Event.Status.ON_SALE,
                'is_featured': True,
                'age_restriction': 'All Ages',
                'video_url': 'https://www.youtube.com/watch?v=TUVcZfQe-Kw',
                'description': 'Experience the electrifying disco pop spectacle of Dua Lipa. Non-stop choreography, euphoric lights, and high-energy anthems by the seaside at Beach City Stadium.',
                'terms_conditions': terms_text,
                'categories': [
                    ('VIP Early Entry', 'First access to Festival floor, soundcheck access & exclusive tote bag', Decimal('6200000'), 200, 65, 2),
                    ('Festival (General Admission)', 'Standing dancefloor surrounding the extended catwalk', Decimal('2750000'), 3500, 920, 4),
                    ('Tribune Tier A', 'Center elevated reserved seating', Decimal('2100000'), 1800, 410, 4),
                    ('Tribune Tier B', 'Upper side grandstand seating', Decimal('1500000'), 2200, 780, 4),
                ]
            },
            {
                'title': 'Arctic Monkeys Asia Tour — Jakarta Exclusive',
                'slug': 'arctic-monkeys-asia-tour-jakarta',
                'venue': venues_map['Beach City International Stadium (BCIS)'],
                'artists': [artists_map['Arctic Monkeys']],
                'start_time': now + timedelta(days=12, hours=20),
                'end_time': now + timedelta(days=12, hours=23),
                'doors_open': now + timedelta(days=12, hours=17),
                'status': Event.Status.SOLD_OUT,
                'is_featured': True,
                'age_restriction': '15+',
                'video_url': 'https://www.youtube.com/watch?v=bpOSxM0TFV8',
                'description': 'The iconic rock titans Arctic Monkeys return for an exclusive one-night-only performance showcasing their greatest discography from garage rock to cinematic lounge rock.',
                'terms_conditions': terms_text,
                'categories': [
                    ('Festival A (Front Pit)', 'Standing area directly adjacent to the stage', Decimal('3800000'), 2500, 0, 4),
                    ('Festival B (Standing)', 'General standing zone with full stage view', Decimal('2600000'), 4000, 0, 4),
                    ('Tribune Seated', 'Side grandstand numbered seating', Decimal('1800000'), 2000, 0, 4),
                ]
            },
            {
                'title': 'NIKI: Buzz World Tour 2026 Jakarta',
                'slug': 'niki-buzz-world-tour-jakarta',
                'venue': venues_map['Tennis Indoor Senayan'],
                'artists': [artists_map['NIKI']],
                'start_time': now + timedelta(days=70, hours=19),
                'end_time': now + timedelta(days=70, hours=22),
                'doors_open': now + timedelta(days=70, hours=16),
                'status': Event.Status.PUBLISHED,
                'is_featured': False,
                'age_restriction': 'All Ages',
                'video_url': 'https://www.youtube.com/watch?v=R9j0mCqA9gM',
                'description': 'Homecoming headline concert for global superstar NIKI. A soulful and intimate stadium concert celebrating the release of the acclaimed BUZZ album with special guest openers.',
                'terms_conditions': terms_text,
                'categories': [
                    ('VIP Soundcheck Pass', 'Soundcheck experience, priority queue & autographed tour poster', Decimal('4500000'), 150, 40, 2),
                    ('Festival Standing', 'Standing arena surrounding main acoustic stage', Decimal('1850000'), 2000, 580, 4),
                    ('Tribune Upper', 'Upper tier numbered seating', Decimal('1250000'), 1500, 420, 4),
                ]
            },
            {
                'title': 'RADWIMPS World Tour 2026 in Jakarta',
                'slug': 'radwimps-world-tour-jakarta',
                'venue': venues_map['JIExpo Kemayoran Arena'],
                'artists': [artists_map['RADWIMPS']],
                'start_time': now + timedelta(days=85, hours=20),
                'end_time': now + timedelta(days=85, hours=23),
                'doors_open': now + timedelta(days=85, hours=17),
                'status': Event.Status.PUBLISHED,
                'is_featured': False,
                'age_restriction': 'All Ages',
                'video_url': 'https://www.youtube.com/watch?v=a2GujJZfXpg',
                'description': 'Japan\'s premier rock pioneers RADWIMPS return with full orchestral arrangements, visual mapping, and stirring anime theme songs that defined modern cinematic music.',
                'terms_conditions': terms_text,
                'categories': [
                    ('Festival VIP', 'Front stage standing area + official tour tee', Decimal('3200000'), 500, 180, 2),
                    ('Festival Regular', 'Main hall general standing area', Decimal('1950000'), 3500, 1200, 4),
                    ('Tribune Center', 'Numbered tiered seating in central row', Decimal('1650000'), 1500, 490, 4),
                ]
            },
            {
                'title': 'Wave to Earth — Play With Earth Tour Jakarta',
                'slug': 'wave-to-earth-play-with-earth-tour',
                'venue': venues_map['Tennis Indoor Senayan'],
                'artists': [artists_map['Wave to Earth']],
                'start_time': now + timedelta(days=100, hours=19, minutes=30),
                'end_time': now + timedelta(days=100, hours=22),
                'doors_open': now + timedelta(days=100, hours=16, minutes=30),
                'status': Event.Status.ON_SALE,
                'is_featured': False,
                'age_restriction': 'All Ages',
                'video_url': 'https://www.youtube.com/watch?v=Uq9Wv4C1BvU',
                'description': 'Immerse in warm analog jazz tones, gentle indie pop melodies, and emotional guitar riffs as Korean indie sensation Wave to Earth performs their complete discography.',
                'terms_conditions': terms_text,
                'categories': [
                    ('VIP Meet & Greet', 'Group photo session, VIP pit & laminate', Decimal('3600000'), 100, 12, 2),
                    ('Festival GA', 'Ground floor general admission', Decimal('1600000'), 2200, 670, 4),
                    ('Tribune Seated', 'Upper grandstand seating', Decimal('1100000'), 1200, 350, 4),
                ]
            },
        ]

        for edata in events_data:
            artists_list = edata.pop('artists')
            categories_list = edata.pop('categories')
            
            event, created = Event.objects.update_or_create(
                slug=edata['slug'],
                defaults=edata
            )
            event.artists.set(artists_list)

            # Ticket categories
            for cname, cdesc, cprice, ctotal, cavail, cmax in categories_list:
                TicketCategory.objects.update_or_create(
                    event=event,
                    name=cname,
                    defaults={
                        'description': cdesc,
                        'price': cprice,
                        'total_quota': ctotal,
                        'available_quota': cavail,
                        'max_per_order': cmax,
                        'sales_start_time': now - timedelta(days=10),
                        'sales_end_time': event.start_time,
                        'is_active': True,
                    }
                )

        self.stdout.write(self.style.SUCCESS(f"[OK] {len(events_data)} Concert Events & Categories synchronized"))

        # 5. Customer Wishlist, Orders, Tickets, and Notifications
        coldplay_event = Event.objects.get(slug='coldplay-music-of-the-spheres-world-tour-jakarta')
        bruno_event = Event.objects.get(slug='bruno-mars-live-in-jakarta-2026')
        dua_event = Event.objects.get(slug='dua-lipa-radical-optimism-tour-jakarta')

        # Wishlists
        Wishlist.objects.get_or_create(user=customer_user, event=coldplay_event)
        Wishlist.objects.get_or_create(user=customer_user, event=bruno_event)

        # Order & Tickets for testing
        cat1 = coldplay_event.ticket_categories.filter(name__icontains='CAT 1').first()
        if cat1:
            order, o_created = Order.objects.get_or_create(
                user=customer_user,
                status=Order.Status.PAID,
                defaults={
                    'total_amount': cat1.price * 2,
                    'admin_fee': Decimal('50000'),
                    'tax_amount': (cat1.price * 2) * Decimal('0.10'),
                    'grand_total': (cat1.price * 2) + Decimal('50000') + ((cat1.price * 2) * Decimal('0.10')),
                    'paid_at': now - timedelta(days=2),
                }
            )
            
            item, _ = OrderItem.objects.get_or_create(
                order=order,
                ticket_category=cat1,
                defaults={
                    'quantity': 2,
                    'unit_price': cat1.price,
                    'subtotal': cat1.price * 2,
                }
            )

            # Tickets
            t1, _ = Ticket.objects.get_or_create(
                order_item=item,
                category=cat1,
                holder_name='Arya Pratama',
                defaults={
                    'holder_email': 'arya@vibetix.com',
                    'holder_id_number': '3171012345670001',
                    'status': Ticket.Status.ISSUED,
                }
            )
            t2, _ = Ticket.objects.get_or_create(
                order_item=item,
                category=cat1,
                holder_name='Sarah Clarissa',
                defaults={
                    'holder_email': 'sarah@vibetix.com',
                    'holder_id_number': '3171012345670002',
                    'status': Ticket.Status.ISSUED,
                }
            )

        # Notifications
        notifs_data = [
            {
                'title': 'Ticket Confirmation: Coldplay Live in Jakarta',
                'message': 'Your order for 2x CAT 1 (Numbered Seating) has been confirmed and paid. Your tickets are issued and ready in My Tickets.',
                'notification_type': Notification.NotificationType.ORDER,
                'is_read': False,
            },
            {
                'title': 'Presale Alert: Bruno Mars Live in Jakarta 2026',
                'message': 'General ticket sales for Bruno Mars Live in Jakarta 2026 are now open! Limited VIP packages remaining.',
                'notification_type': Notification.NotificationType.PROMO,
                'is_read': False,
            },
            {
                'title': 'Gate Schedule Update: Gelora Bung Karno',
                'message': 'Doors open for stadium entry will begin at 16:00 WIB. Please bring your government photo ID and digital ticket pass.',
                'notification_type': Notification.NotificationType.EVENT,
                'is_read': True,
            },
            {
                'title': 'Welcome to VibeTix Community',
                'message': 'Thank you for joining VibeTix — the official home for authentic live music concert ticketing.',
                'notification_type': Notification.NotificationType.SYSTEM,
                'is_read': True,
            },
        ]

        for ndata in notifs_data:
            Notification.objects.get_or_create(
                user=customer_user,
                title=ndata['title'],
                defaults=ndata
            )

        self.stdout.write(self.style.SUCCESS("[OK] Customer test data seeded: Wishlist, Orders, Tickets, Notifications"))
        self.stdout.write(self.style.SUCCESS("[OK] VibeTix database seeding completed successfully!"))
