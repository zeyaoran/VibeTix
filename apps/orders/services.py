from decimal import Decimal
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from apps.events.models import Event
from apps.tickets.models import TicketCategory
from apps.tickets.services import generate_tickets_for_order
from apps.orders.models import Order, OrderItem, Cart, CartItem
from apps.payments.models import Payment
from apps.notifications.models import Notification

# Platform calculation constants
ADMIN_FEE = Decimal('10000.00')  # Flat Rp 10,000 platform service fee
TAX_RATE = Decimal('0.10')       # 10% Government Entertainment Tax


def calculate_order_totals(subtotal: Decimal) -> Dict[str, Decimal]:
    """
    Authoritative server-side calculation for subtotal, platform admin fee, tax, and grand total.
    """
    subtotal = Decimal(str(subtotal))
    if subtotal > 0:
        admin_fee = ADMIN_FEE
        tax_amount = (subtotal * TAX_RATE).quantize(Decimal('1.00'))
        grand_total = subtotal + admin_fee + tax_amount
    else:
        admin_fee = Decimal('0.00')
        tax_amount = Decimal('0.00')
        grand_total = Decimal('0.00')

    return {
        'subtotal': subtotal,
        'admin_fee': admin_fee,
        'tax_amount': tax_amount,
        'grand_total': grand_total,
    }


def validate_ticket_category_for_purchase(category: TicketCategory, quantity: int) -> Tuple[bool, Optional[str]]:
    """
    Validates ticket category status, sales window, quota availability, and max per order.
    """
    now = timezone.now()

    if not category.is_active:
        return False, f"Ticket tier '{category.name}' is currently inactive."

    if category.event.status not in [Event.Status.ON_SALE, Event.Status.PUBLISHED]:
        return False, f"Event '{category.event.title}' is not currently accepting ticket sales."

    if now < category.sales_start_time:
        return False, f"Sales for '{category.name}' have not started yet (Opens on {category.sales_start_time.strftime('%d %b %Y, %H:%M')})."

    if now > category.sales_end_time:
        return False, f"Sales for '{category.name}' have already ended (Closed on {category.sales_end_time.strftime('%d %b %Y, %H:%M')})."

    if quantity < 1:
        return False, "Ticket quantity must be at least 1."

    if quantity > category.max_per_order:
        return False, f"Maximum limit for '{category.name}' is {category.max_per_order} tickets per transaction."

    if category.available_quota < quantity:
        if category.available_quota <= 0:
            return False, f"'{category.name}' is currently sold out."
        return False, f"Insufficient quota for '{category.name}'. Only {category.available_quota} ticket(s) remaining."

    return True, None


def get_or_create_user_cart(user) -> Cart:
    """
    Retrieves or initializes the Shopping Cart instance for the authenticated user.
    """
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


def create_order_from_cart(user, attendee_names: Optional[Dict[int, List[str]]] = None) -> Tuple[Optional[Order], Optional[str]]:
    """
    Creates a real PENDING Order from all items in the user's cart.
    Applies select_for_update row-level locking on TicketCategory rows to prevent overselling.
    """
    cart = get_or_create_user_cart(user)
    cart_items = list(cart.items.select_related('ticket_category__event').all())

    if not cart_items:
        return None, "Your shopping cart is currently empty."

    with transaction.atomic():
        # Collect and lock categories
        category_ids = [item.ticket_category_id for item in cart_items]
        locked_categories = {
            cat.id: cat
            for cat in TicketCategory.objects.select_for_update().filter(id__in=category_ids)
        }

        # Validate each item against locked category state
        subtotal = Decimal('0.00')
        for item in cart_items:
            cat = locked_categories.get(item.ticket_category_id)
            if not cat:
                return None, f"Ticket category '{item.ticket_category.name}' is no longer available."

            is_valid, error_msg = validate_ticket_category_for_purchase(cat, item.quantity)
            if not is_valid:
                return None, error_msg

            item_subtotal = cat.price * item.quantity
            subtotal += item_subtotal

        # Calculate authoritative financials
        totals = calculate_order_totals(subtotal)

        # Create Order
        order = Order.objects.create(
            user=user,
            status=Order.Status.PENDING,
            total_amount=totals['subtotal'],
            admin_fee=totals['admin_fee'],
            tax_amount=totals['tax_amount'],
            grand_total=totals['grand_total'],
            expires_at=timezone.now() + timedelta(minutes=30),
        )

        # Create OrderItems and decrement category available quotas
        for item in cart_items:
            cat = locked_categories[item.ticket_category_id]
            unit_price = cat.price
            item_subtotal = unit_price * item.quantity

            OrderItem.objects.create(
                order=order,
                ticket_category=cat,
                quantity=item.quantity,
                unit_price=unit_price,
                subtotal=item_subtotal,
            )

            # Safely decrement available quota
            cat.available_quota -= item.quantity
            cat.save(update_fields=['available_quota', 'updated_at'])

        # Create Payment record foundation (Pending Midtrans integration)
        Payment.objects.create(
            order=order,
            payment_method=Payment.PaymentMethod.MIDTRANS,
            gross_amount=order.grand_total,
            status=Payment.Status.PENDING,
        )

        # Clear Cart
        cart.items.all().delete()

        # Send User Notification
        event_names = ", ".join(set(item.ticket_category.event.title for item in cart_items))
        Notification.objects.create(
            user=user,
            title=f"Order Created: #{order.order_number}",
            message=f"Your order for '{event_names}' has been placed. Please complete payment before {order.expires_at.strftime('%H:%M WIB')} to secure your passes.",
            notification_type=Notification.NotificationType.ORDER,
        )

        return order, None


def mark_order_as_paid(order: Order) -> Order:
    """
    Marks a PENDING order as PAID, updates payment record, generates authentic tickets,
    and sends confirmation notification.
    """
    with transaction.atomic():
        order.status = Order.Status.PAID
        order.paid_at = timezone.now()
        order.save(update_fields=['status', 'paid_at', 'updated_at'])

        # Update Payment
        if hasattr(order, 'payment'):
            payment = order.payment
            payment.status = Payment.Status.SETTLEMENT
            payment.save(update_fields=['status', 'updated_at'])
        else:
            Payment.objects.create(
                order=order,
                payment_method=Payment.PaymentMethod.MIDTRANS,
                gross_amount=order.grand_total,
                status=Payment.Status.SETTLEMENT,
            )

        # Generate authentic Tickets
        tickets = generate_tickets_for_order(order)

        # Send Success Notification
        first_item = order.items.select_related('ticket_category__event').first()
        event_title = first_item.ticket_category.event.title if first_item else "Concert"
        Notification.objects.create(
            user=order.user,
            title=f"Payment Successful: #{order.order_number}",
            message=f"Your payment of Rp {order.grand_total:,.0f} for '{event_title}' has been confirmed! {len(tickets)} digital passes have been added to your ticket wallet.",
            notification_type=Notification.NotificationType.ORDER,
        )

        return order
