from django.db import models
from apps.orders.models import Order


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SETTLEMENT = 'SETTLEMENT', 'Settlement / Paid'
        CAPTURE = 'CAPTURE', 'Captured'
        DENY = 'DENY', 'Denied'
        CANCEL = 'CANCEL', 'Cancelled'
        EXPIRE = 'EXPIRE', 'Expired'
        REFUND = 'REFUND', 'Refunded'

    class PaymentMethod(models.TextChoices):
        MIDTRANS = 'MIDTRANS', 'Midtrans Gateway'
        BANK_TRANSFER = 'BANK_TRANSFER', 'Bank Transfer (VA)'
        CREDIT_CARD = 'CREDIT_CARD', 'Credit Card'
        E_WALLET = 'E_WALLET', 'E-Wallet (GoPay/OVO/ShopeePay)'
        QRIS = 'QRIS', 'QRIS'

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    transaction_id = models.CharField(max_length=100, blank=True, null=True, db_index=True)
    payment_method = models.CharField(
        max_length=30,
        choices=PaymentMethod.choices,
        default=PaymentMethod.MIDTRANS
    )
    gross_amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True
    )
    payment_type_detail = models.CharField(max_length=50, blank=True, help_text="e.g. bca_va, gopay, qris")
    payment_url = models.URLField(max_length=500, blank=True, help_text="Payment redirect or Snap URL")
    raw_response = models.JSONField(blank=True, null=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return f"Payment #{self.id} for {self.order.order_number} - {self.get_status_display()}"
