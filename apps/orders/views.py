from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import Order


@login_required
def order_list_view(request):
    """
    Order history foundation page displaying all real orders made by the user.
    """
    queryset = Order.objects.filter(
        user=request.user
    ).prefetch_related(
        'items__ticket_category__event__venue',
        'items__ticket_category__event__artists'
    ).order_by('-created_at')

    status_filter = request.GET.get('status', '').strip()
    if status_filter in dict(Order.Status.choices):
        queryset = queryset.filter(status=status_filter)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'orders': page_obj.object_list,
        'status_filter': status_filter,
        'total_count': paginator.count,
    }
    return render(request, 'orders/order_list.html', context)


@login_required
def order_detail_view(request, order_number):
    """
    Individual Order summary and itemized receipt breakdown with ownership verification.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related(
            'items__ticket_category__event__venue',
            'items__ticket_category__event__artists',
            'items__tickets'
        ),
        order_number=order_number,
        user=request.user
    )

    context = {
        'order': order,
        'items': order.items.all(),
    }
    return render(request, 'orders/order_detail.html', context)
