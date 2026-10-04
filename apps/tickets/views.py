from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404
from .models import Ticket


@login_required
def my_tickets_view(request):
    """
    My Tickets page displaying all authentic tickets owned by the authenticated user
    resolved through User -> Order -> OrderItem -> Ticket.
    """
    queryset = Ticket.objects.filter(
        order_item__order__user=request.user
    ).select_related(
        'order_item__order',
        'category__event__venue'
    ).prefetch_related(
        'category__event__artists'
    ).order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status', '').strip()
    if status_filter in dict(Ticket.Status.choices):
        queryset = queryset.filter(status=status_filter)

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(ticket_code__icontains=q) |
            Q(category__event__title__icontains=q) |
            Q(holder_name__icontains=q)
        )

    paginator = Paginator(queryset, 8)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'tickets': page_obj.object_list,
        'status_filter': status_filter,
        'q': q,
        'total_count': paginator.count,
    }
    return render(request, 'tickets/my_tickets.html', context)


@login_required
def ticket_detail_view(request, ticket_code):
    """
    Individual ticket pass detail modal / view with ownership verification.
    """
    ticket = get_object_or_404(
        Ticket.objects.select_related(
            'order_item__order',
            'category__event__venue'
        ).prefetch_related(
            'category__event__artists'
        ),
        ticket_code=ticket_code,
        order_item__order__user=request.user
    )

    context = {
        'ticket': ticket,
    }
    return render(request, 'tickets/ticket_detail.html', context)
