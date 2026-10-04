import uuid
from typing import List, Optional, Dict
from django.db import transaction
from apps.tickets.models import Ticket


def generate_tickets_for_order(order, holder_names: Optional[Dict[int, List[str]]] = None) -> List[Ticket]:
    """
    Generate authentic unique Ticket passes for all OrderItems of an Order.
    Can be called upon payment settlement or order fulfillment.
    """
    created_tickets = []
    
    with transaction.atomic():
        for item in order.items.select_related('ticket_category').all():
            existing_count = item.tickets.count()
            needed = item.quantity - existing_count
            
            if needed <= 0:
                continue

            item_holder_names = []
            if holder_names and item.id in holder_names:
                item_holder_names = holder_names[item.id]

            for i in range(needed):
                # Fallback to order user's name if specific attendee name not provided
                if i < len(item_holder_names) and item_holder_names[i].strip():
                    holder_name = item_holder_names[i].strip()
                else:
                    holder_name = order.user.get_full_name() or order.user.username

                holder_email = order.user.email

                ticket = Ticket(
                    order_item=item,
                    category=item.ticket_category,
                    holder_name=holder_name,
                    holder_email=holder_email,
                    status=Ticket.Status.ISSUED,
                )
                ticket.save()
                created_tickets.append(ticket)

    return created_tickets
