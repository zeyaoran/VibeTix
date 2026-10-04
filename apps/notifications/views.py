from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from .models import Notification


@login_required
def notification_list_view(request):
    """
    User notification center displaying alerts, ticket receipts,
    and event announcements for the authenticated user.
    """
    queryset = Notification.objects.filter(user=request.user).order_by('-created_at')

    filter_type = request.GET.get('type', '').strip()
    filter_status = request.GET.get('status', '').strip()

    if filter_type in dict(Notification.NotificationType.choices):
        queryset = queryset.filter(notification_type=filter_type)

    if filter_status == 'unread':
        queryset = queryset.filter(is_read=False)
    elif filter_status == 'read':
        queryset = queryset.filter(is_read=True)

    paginator = Paginator(queryset, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'filter_type': filter_type,
        'filter_status': filter_status,
        'unread_count': unread_count,
        'total_count': paginator.count,
    }
    return render(request, 'notifications/notification_list.html', context)


@login_required
@require_POST
def mark_notification_read_view(request, notification_id):
    """
    Mark a single notification as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.is_read = True
    notification.save()

    unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'unread_count': unread_count,
            'notification_id': notification.id,
        })

    return redirect('notifications:list')


@login_required
@require_POST
def mark_all_notifications_read_view(request):
    """
    Mark all unread notifications for the user as read.
    """
    updated_count = Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or 'application/json' in request.headers.get('Accept', ''):
        return JsonResponse({
            'success': True,
            'updated_count': updated_count,
            'unread_count': 0,
        })

    messages.success(request, "All notifications marked as read.")
    return redirect('notifications:list')
