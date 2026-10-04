import calendar
from datetime import datetime, date
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.events.models import Event, Artist, Venue
from .models import Wishlist


def home_view(request):
    """
    Editorial dynamic homepage.
    Hero spotlight, live discovery search, upcoming events, featured events,
    top artists, interactive calendar preview, and live video teaser showcase.
    """
    now = timezone.now()

    # Hero featured event
    hero_event = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE],
        is_featured=True
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').first()

    # If no featured event, pick earliest upcoming published event
    if not hero_event:
        hero_event = Event.objects.filter(
            status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE]
        ).select_related('venue').prefetch_related('artists', 'ticket_categories').first()

    # Featured events carousel / grid (excluding hero)
    featured_events = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE],
        is_featured=True
    ).select_related('venue').prefetch_related('artists', 'ticket_categories')
    if hero_event:
        featured_events = featured_events.exclude(id=hero_event.id)[:6]

    # Upcoming events
    upcoming_events = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE]
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').order_by('start_time')[:6]

    # Performing artists spotlight
    artists = Artist.objects.all().order_by('name')[:8]

    # Calendar preview (next 4 upcoming scheduled events)
    calendar_preview_events = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT],
        start_time__gte=now
    ).select_related('venue').prefetch_related('artists').order_by('start_time')[:5]

    # Video Experience section: real event with video_url
    video_event = Event.objects.filter(
        video_url__isnull=False
    ).exclude(video_url='').select_related('venue').prefetch_related('artists').first()

    # Wishlist IDs for authenticated user
    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'hero_event': hero_event,
        'featured_events': featured_events,
        'upcoming_events': upcoming_events,
        'artists': artists,
        'calendar_preview_events': calendar_preview_events,
        'video_event': video_event,
        'total_events_count': Event.objects.count(),
        'total_artists_count': Artist.objects.count(),
        'total_venues_count': Venue.objects.count(),
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'core/home.html', context)


def calendar_view(request):
    """
    Dedicated interactive event calendar page using actual Event.start_time values.
    Supports month/year navigation and date agenda filtering.
    """
    today = timezone.localdate()

    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except (ValueError, TypeError):
        year = today.year
        month = today.month

    # Validate month range
    if month < 1:
        month = 12
        year -= 1
    elif month > 12:
        month = 1
        year += 1

    # Fetch real events in selected month
    month_events = Event.objects.filter(
        status__in=[Event.Status.PUBLISHED, Event.Status.ON_SALE, Event.Status.SOLD_OUT],
        start_time__year=year,
        start_time__month=month
    ).select_related('venue').prefetch_related('artists', 'ticket_categories').order_by('start_time')

    # Map events by day number
    events_by_day = {}
    for event in month_events:
        day = timezone.localtime(event.start_time).day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append(event)

    # Calendar matrix calculation
    cal = calendar.Calendar(firstweekday=0)  # Monday first
    month_days = cal.monthdayscalendar(year, month)

    calendar_grid = []
    for week in month_days:
        week_data = []
        for day in week:
            is_today = (year == today.year and month == today.month and day == today.day)
            day_events = events_by_day.get(day, [])
            week_data.append({
                'day': day,
                'is_today': is_today,
                'has_events': len(day_events) > 0,
                'events_count': len(day_events),
                'events': day_events,
            })
        calendar_grid.append(week_data)

    # Calculate previous and next month links
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    month_name = calendar.month_name[month]

    user_wishlist_ids = set()
    if request.user.is_authenticated:
        user_wishlist_ids = set(Wishlist.objects.filter(user=request.user).values_list('event_id', flat=True))

    context = {
        'year': year,
        'month': month,
        'month_name': month_name,
        'calendar_grid': calendar_grid,
        'month_events': month_events,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
        'today': today,
        'user_wishlist_ids': user_wishlist_ids,
    }
    return render(request, 'core/calendar.html', context)


@login_required
def wishlist_view(request):
    """
    Authenticated user's Wishlist page displaying saved concert events.
    """
    wishlists = Wishlist.objects.filter(
        user=request.user
    ).select_related('event__venue').prefetch_related('event__artists', 'event__ticket_categories').order_by('-created_at')

    user_wishlist_ids = set([w.event_id for w in wishlists])

    context = {
        'wishlists': wishlists,
        'user_wishlist_ids': user_wishlist_ids,
        'total_count': wishlists.count(),
    }
    return render(request, 'core/wishlist.html', context)


@login_required
@require_POST
def wishlist_toggle_view(request, event_id):
    """
    Toggle event in authenticated user's wishlist.
    Supports both AJAX JSON responses and standard POST redirects.
    """
    event = get_object_or_404(Event, id=event_id)
    wishlist_item = Wishlist.objects.filter(user=request.user, event=event).first()

    if wishlist_item:
        wishlist_item.delete()
        is_wishlisted = False
        action_msg = f"Removed '{event.title}' from your wishlist."
    else:
        Wishlist.objects.create(user=request.user, event=event)
        is_wishlisted = True
        action_msg = f"Added '{event.title}' to your wishlist!"

    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    # Check if request is AJAX / JSON request
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'is_wishlisted': is_wishlisted,
            'wishlist_count': wishlist_count,
            'message': action_msg,
        })

    messages.success(request, action_msg)
    next_url = request.POST.get('next', request.META.get('HTTP_REFERER', 'core:wishlist'))
    return redirect(next_url)
