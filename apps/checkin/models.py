from django.conf import settings
from django.db import models
from apps.tickets.models import Ticket


class CheckIn(models.Model):
    ticket = models.OneToOneField(
        Ticket,
        on_delete=models.CASCADE,
        related_name='checkin'
    )
    checked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='checkins_conducted'
    )
    checked_at = models.DateTimeField(auto_now_add=True)
    gate_name = models.CharField(max_length=100, blank=True, default='Main Gate')
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checked_at']
        verbose_name = 'Check-In'
        verbose_name_plural = 'Check-Ins'

    def __str__(self):
        return f"Check-In: {self.ticket.ticket_code} at {self.gate_name} ({self.checked_at.strftime('%Y-%m-%d %H:%M')})"
