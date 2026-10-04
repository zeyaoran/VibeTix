import uuid
from django.db import models
from apps.events.models import Event


class TicketCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='ticket_categories')
    name = models.CharField(max_length=100, help_text="e.g. VIP, CAT 1, CAT 2, Festival")
    description = models.TextField(blank=True, help_text="Benefits, perks, or tier details")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_quota = models.PositiveIntegerField()
    available_quota = models.PositiveIntegerField()
    max_per_order = models.PositiveIntegerField(default=4)
    sales_start_time = models.DateTimeField()
    sales_end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['price']
        verbose_name = 'Ticket Category'
        verbose_name_plural = 'Ticket Categories'
        constraints = [
            models.UniqueConstraint(fields=['event', 'name'], name='unique_event_ticket_category')
        ]

    def __str__(self):
        return f"{self.event.title} - {self.name} (Rp {self.price:,.0f})"

    @property
    def is_sold_out(self):
        return self.available_quota <= 0


class Ticket(models.Model):
    class Status(models.TextChoices):
        ISSUED = 'ISSUED', 'Issued'
        CHECKED_IN = 'CHECKED_IN', 'Checked In'
        CANCELLED = 'CANCELLED', 'Cancelled'
        REFUNDED = 'REFUNDED', 'Refunded'

    ticket_code = models.CharField(max_length=64, unique=True, editable=False, db_index=True)
    order_item = models.ForeignKey('orders.OrderItem', on_delete=models.CASCADE, related_name='tickets')
    category = models.ForeignKey(TicketCategory, on_delete=models.PROTECT, related_name='tickets')
    holder_name = models.CharField(max_length=150)
    holder_email = models.EmailField()
    holder_id_number = models.CharField(max_length=50, blank=True, help_text="KTP/Passport/ID Number")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ISSUED,
        db_index=True
    )
    qr_code_hash = models.CharField(max_length=128, blank=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'

    def save(self, *args, **kwargs):
        if not self.ticket_code:
            self.ticket_code = f"TIX-{uuid.uuid4().hex[:10].upper()}"
        if not self.qr_code_hash:
            self.qr_code_hash = uuid.uuid4().hex
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.ticket_code} - {self.holder_name} ({self.category.name})"
