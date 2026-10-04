from django.db.models import Min, Max, Q, Count
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from .models import Event, Artist, Venue
from apps.core.models import Wishlist


def event_list_view(request):
    """
    Explore Events discovery page with full search, multi-faceted filters,
    sorting, and Django pagination.
    """
    now = timezone.now()
    queryset = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT]
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').annotate(
        min_price=Min('ticket_categories__price')
    )

    # Search Query
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(title__icontains=q) |
            Q(artists__name__icontains=q) |
            Q(venue__name__icontains=q) |
            Q(venue__city__icontains=q) |
            Q(description__icontains=q)
        ).distinct()

    # City Filter
    selected_city = request.GET.get('city', '').strip()
    if selected_city:
        queryset = queryset.filter(venue__city__iexact=selected_city)

    # Genre Filter
    selected_genre = request.GET.get('genre', '').strip()
    if selected_genre:
        queryset = queryset.filter(artists__genre__icontains=selected_genre).distinct()

    # Status Filter
    selected_status = request.GET.get('status', '').strip()
    if selected_status and selected_status in [Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT]:
        queryset = queryset.filter(status=selected_status)

    # Date Range Filter
    date_filter = request.GET.get('date', '').strip()
    if date_filter == 'today':
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        queryset = queryset.filter(start_time__range=(start_of_day, end_of_day))
    elif date_filter == 'this_week':
        end_of_week = now + timedelta(days=7)
        queryset = queryset.filter(start_time__range=(now, end_of_week))
    elif date_filter == 'this_month':
        end_of_month = now + timedelta(days=30)
        queryset = queryset.filter(start_time__range=(now, end_of_month))
    elif date_filter == 'upcoming':
        queryset = queryset.filter(start_time__gte=now)

    # Price Range Filter
    price_min = request.GET.get('price_min', '').strip()
    price_max = request.GET.get('price_max', '').strip()
    if price_min:
        try:
            queryset = queryset.filter(ticket_categories__price__gte=float(price_min)).distinct()
        except ValueError:
            pass
    if price_max:
        try:
            queryset = queryset.filter(ticket_categories__price__lte=float(price_max)).distinct()
        except ValueError:
            pass

    # Sorting
    sort = request.GET.get('sort', 'date_asc').strip()
    if sort == 'date_asc':
        queryset = queryset.order_by('start_time')
    elif sort == 'date_desc':
        queryset = queryset.order_by('-start_time')
    elif sort == 'price_asc':
        queryset = queryset.order_by('min_price', 'start_time')
    elif sort == 'price_desc':
        queryset = queryset.order_by('-min_price', 'start_time')
    elif sort == 'newest':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('start_time')

    # Pagination (9 per page)
    paginator = Paginator(queryset, 9)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    # Filter metadata
    cities = Venue.objects.values_list('city', flat=True).distinct().order_by('city')
    genres_raw = Artist.objects.values_list('genre', flat=True).distinct()
    genres = set()
    for g in genres_raw:
        if g:
            for item in g.split('/'):
                genres.add(item.strip())
    sorted_genres = sorted(list(genres))

    # Wishlisted event IDs for authenticated user
    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'page_obj': page_obj,
        'events': page_obj.object_list,
        'q': q,
        'selected_city': selected_city,
        'selected_genre': selected_genre,
        'selected_status': selected_status,
        'date_filter': date_filter,
        'price_min': price_min,
        'price_max': price_max,
        'sort': sort,
        'cities': cities,
        'genres': sorted_genres,
        'total_count': paginator.count,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'events/event_list.html', context)


def event_detail_view(request, slug):
    """
    Comprehensive dynamic Event Detail page.
    Includes banner, artist relations, venue details, ticket category matrix,
    responsive video trailer player, terms and conditions, and wishlist toggle.
    """
    event = get_object_or_404(
        Event.objects.select_related('venue').prefetch_related('artists', 'ticket_categories'),
        slug=slug
    )

    ticket_categories = event.ticket_categories.filter(is_active=True).order_by('price')
    artists = event.artists.all()
    
    is_wishlisted = False
    if request.user.is_authenticated:
        is_wishlisted = Wishlist.objects.filter(user=request.user, event=event).exists()

    # Similar/related events in same venue or featuring same artists
    related_events = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE]
    ).exclude(id=event.id).filter(
        Q(venue=event.venue) | Q(artists__in=artists)
    ).distinct().select_related('venue').prefetch_related('artists')[:3]

    context = {
        'event': event,
        'ticket_categories': ticket_categories,
        'artists': artists,
        'is_wishlisted': is_wishlisted,
        'related_events': related_events,
    }
    return render(request, 'events/event_detail.html', context)


def artist_list_view(request):
    """
    Editorial artist browsing directory.
    """
    q = request.GET.get('q', '').strip()
    artists_qs = Artist.objects.annotate(
        events_count=Count('events', filter=Q(events__status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE]))
    ).order_by('name')

    if q:
        artists_qs = artists_qs.filter(Q(name__icontains=q) | Q(genre__icontains=q))

    paginator = Paginator(artists_qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'artists': page_obj.object_list,
        'q': q,
        'total_count': paginator.count,
    }
    return render(request, 'events/artist_list.html', context)


def artist_detail_view(request, slug):
    """
    Artist profile page displaying biography, genre, social links,
    and all upcoming events featuring this artist.
    """
    artist = get_object_or_404(Artist, slug=slug)
    upcoming_events = artist.events.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT]
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').order_by('start_time')

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'artist': artist,
        'upcoming_events': upcoming_events,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'events/artist_detail.html', context)


def venue_list_view(request):
    """
    Venue browsing directory with capacities and cities.
    """
    q = request.GET.get('q', '').strip()
    city_filter = request.GET.get('city', '').strip()

    venues_qs = Venue.objects.annotate(
        events_count=Count('events', filter=Q(events__status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE]))
    ).order_by('city', 'name')

    if q:
        venues_qs = venues_qs.filter(Q(name__icontains=q) | Q(address__icontains=q) | Q(city__icontains=q))
    if city_filter:
        venues_qs = venues_qs.filter(city__iexact=city_filter)

    cities = Venue.objects.values_list('city', flat=True).distinct().order_by('city')

    paginator = Paginator(venues_qs, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'venues': page_obj.object_list,
        'q': q,
        'city_filter': city_filter,
        'cities': cities,
        'total_count': paginator.count,
    }
    return render(request, 'events/venue_list.html', context)


def venue_detail_view(request, slug):
    """
    Venue detail page displaying location, address, capacity,
    and all upcoming scheduled concerts at this venue.
    """
    venue = get_object_or_404(Venue, slug=slug)
    upcoming_events = venue.events.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT]
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').order_by('start_time')

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'venue': venue,
        'upcoming_events': upcoming_events,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'events/venue_detail.html', context)
