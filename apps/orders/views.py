from decimal import Decimal
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST, require_http_methods
from apps.tickets.models import TicketCategory
from .models import Order, OrderItem, Cart, CartItem
from .services import (
    calculate_order_totals,
    validate_ticket_category_for_purchase,
    get_or_create_user_cart,
    create_order_from_cart,
    mark_order_as_paid,
)


@login_required
def cart_view(request):
    """
    Shopping cart foundation view. Displays all active items in user's cart
    with category details, quantities, item subtotals, and calculated platform fees.
    """
    cart = get_or_create_user_cart(request.user)
    items = cart.items.select_related(
        'ticket_category__event__venue'
    ).order_by('created_at')

    # Re-validate items for display warnings
    validated_items = []
    for item in items:
        is_valid, error_msg = validate_ticket_category_for_purchase(
            item.ticket_category,
            item.quantity
        )
        validated_items.append({
            'item': item,
            'is_valid': is_valid,
            'error_msg': error_msg,
        })

    totals = calculate_order_totals(cart.subtotal)

    context = {
        'cart': cart,
        'validated_items': validated_items,
        'items': items,
        'totals': totals,
    }
    return render(request, 'orders/cart.html', context)


@login_required
@require_POST
def cart_add_view(request, category_id):
    """
    Adds a ticket category to the user's shopping cart with strict quota and sales validations.
    Supports standard form submission, Buy Now direct redirect, and AJAX requests.
    """
    category = get_object_or_404(TicketCategory.objects.select_related('event'), id=category_id)

    try:
        quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        quantity = 1

    # Validate category and requested quantity
    is_valid, error_msg = validate_ticket_category_for_purchase(category, quantity)
    if not is_valid:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('events:detail', slug=category.event.slug)

    cart = get_or_create_user_cart(request.user)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        ticket_category=category,
        defaults={'quantity': quantity}
    )

    if not created:
        new_quantity = cart_item.quantity + quantity
        # Validate combined quantity
        combined_valid, combined_error = validate_ticket_category_for_purchase(category, new_quantity)
        if not combined_valid:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': combined_error}, status=400)
            messages.warning(request, combined_error)
            return redirect('orders:cart')

        cart_item.quantity = new_quantity
        cart_item.save(update_fields=['quantity', 'updated_at'])

    is_buy_now = request.POST.get('buy_now') in ['1', 'true', 'True']

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'message': f"Added {quantity}x {category.name} tickets to cart.",
            'cart_items_count': cart.total_items,
            'redirect_url': '/checkout/' if is_buy_now else '/cart/'
        })

    messages.success(request, f"Added {quantity}x {category.name} tickets for '{category.event.title}' to your cart.")

    if is_buy_now:
        return redirect('orders:checkout')
    return redirect('orders:cart')


@login_required
@require_POST
def cart_update_view(request, item_id):
    """
    Updates the quantity of a specific item in the user's cart with quota validation.
    """
    cart = get_or_create_user_cart(request.user)
    cart_item = get_object_or_404(CartItem.objects.select_related('ticket_category'), id=item_id, cart=cart)

    try:
        new_quantity = int(request.POST.get('quantity', 1))
    except (ValueError, TypeError):
        new_quantity = 1

    if new_quantity <= 0:
        cart_item.delete()
        messages.info(request, f"Removed '{cart_item.ticket_category.name}' from your cart.")
        return redirect('orders:cart')

    is_valid, error_msg = validate_ticket_category_for_purchase(cart_item.ticket_category, new_quantity)
    if not is_valid:
        messages.error(request, error_msg)
        return redirect('orders:cart')

    cart_item.quantity = new_quantity
    cart_item.save(update_fields=['quantity', 'updated_at'])
    messages.success(request, f"Updated quantity for '{cart_item.ticket_category.name}' to {new_quantity}.")
    return redirect('orders:cart')


@login_required
@require_POST
def cart_remove_view(request, item_id):
    """
    Removes a single item from the authenticated user's cart.
    """
    cart = get_or_create_user_cart(request.user)
    cart_item = get_object_or_404(CartItem.objects.select_related('ticket_category'), id=item_id, cart=cart)
    cat_name = cart_item.ticket_category.name
    cart_item.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        totals = calculate_order_totals(cart.subtotal)
        return JsonResponse({
            'success': True,
            'message': f"Removed {cat_name} from cart.",
            'cart_items_count': cart.total_items,
            'subtotal': float(totals['subtotal']),
            'grand_total': float(totals['grand_total']),
        })

    messages.info(request, f"Removed '{cat_name}' from your cart.")
    return redirect('orders:cart')


@login_required
@require_POST
def cart_clear_view(request):
    """
    Empties all items from the authenticated user's cart.
    """
    cart = get_or_create_user_cart(request.user)
    cart.items.all().delete()
    messages.info(request, "Your shopping cart has been cleared.")
    return redirect('orders:cart')


@login_required
def checkout_view(request):
    """
    Authoritative checkout page displaying real database order breakdown,
    fees, taxes, and customer billing information before order creation.
    """
    cart = get_or_create_user_cart(request.user)
    items = list(cart.items.select_related('ticket_category__event__venue').all())

    if not items:
        messages.warning(request, "Your cart is currently empty. Please select tickets to proceed to checkout.")
        return redirect('events:list')

    # Validate each item before allowing checkout
    for item in items:
        is_valid, error_msg = validate_ticket_category_for_purchase(item.ticket_category, item.quantity)
        if not is_valid:
            messages.error(request, f"Cannot proceed: {error_msg}")
            return redirect('orders:cart')

    totals = calculate_order_totals(cart.subtotal)

    context = {
        'cart': cart,
        'items': items,
        'totals': totals,
        'user': request.user,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
@require_POST
def checkout_process_view(request):
    """
    Processes final checkout confirmation.
    Executes atomic database transaction, creates Order, OrderItems, decrements quotas,
    and initializes Payment record.
    """
    order, error_msg = create_order_from_cart(request.user)

    if error_msg or not order:
        messages.error(request, error_msg or "Failed to place order. Please try again.")
        return redirect('orders:cart')

    messages.success(request, f"Order #{order.order_number} has been created successfully! Please review payment details.")
    return redirect('orders:detail', order_number=order.order_number)


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
    Individual Order summary, itemized receipt breakdown, and payment status with ownership verification.
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
        'debug': settings.DEBUG,
    }
    return render(request, 'orders/order_detail.html', context)


@login_required
@require_POST
def simulate_payment_view(request, order_number):
    """
    Phase 3 testing/verification helper: Simulates payment settlement for an authentic PENDING order,
    transitioning it to PAID and generating real ticket passes.
    """
    order = get_object_or_404(
        Order.objects.prefetch_related('items__ticket_category'),
        order_number=order_number,
        user=request.user
    )

    if order.status != Order.Status.PENDING:
        messages.info(request, f"Order #{order.order_number} is already {order.get_status_display()}.")
        return redirect('orders:detail', order_number=order.order_number)

    mark_order_as_paid(order)
    messages.success(request, f"Payment confirmed for #{order.order_number}! Your digital tickets have been generated and issued to your wallet.")
    return redirect('orders:detail', order_number=order.order_number)
