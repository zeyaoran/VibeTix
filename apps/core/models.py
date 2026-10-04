from django.conf import settings
from django.db import models
from apps.events.models import Event


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wishlists'
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='favorited_by'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Wishlist'
        verbose_name_plural = 'Wishlists'
        constraints = [
            models.UniqueConstraint(fields=['user', 'event'], name='unique_user_event_wishlist')
        ]

    def __str__(self):
        return f"{self.user.username} -> {self.event.title}"
