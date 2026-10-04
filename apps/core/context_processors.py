from apps.notifications.models import Notification
from apps.core.models import Wishlist


def vibetix_context(request):
    """
    Global context processor for VibeTix user-facing platform.
    Provides unread notification counts and wishlist counts for authenticated users.
    """
    if request.user.is_authenticated:
        unread_notifications_count = Notification.objects.filter(
            user=request.user,
            is_read=False
        ).count()
        wishlist_count = Wishlist.objects.filter(
            user=request.user
        ).count()
        return {
            'unread_notifications_count': unread_notifications_count,
            'wishlist_count': wishlist_count,
        }
    return {
        'unread_notifications_count': 0,
        'wishlist_count': 0,
    }
