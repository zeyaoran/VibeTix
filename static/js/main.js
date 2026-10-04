/**
 * VibeTix User-Facing Platform — Client-Side Utilities
 * Lightweight enhancements for AJAX wishlist, notifications, video interaction & calendar
 */

document.addEventListener('DOMContentLoaded', () => {
    // CSRF Helper for fetch requests
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    // Wishlist Toggle Buttons (AJAX)
    document.querySelectorAll('.js-wishlist-toggle').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const eventId = btn.dataset.eventId;
            const toggleUrl = btn.dataset.url || `/wishlist/toggle/${eventId}/`;

            if (!eventId) return;

            try {
                const response = await fetch(toggleUrl, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }

                if (response.ok) {
                    const data = await response.json();
                    
                    // Update all buttons for this eventId
                    document.querySelectorAll(`.js-wishlist-toggle[data-event-id="${eventId}"]`).forEach(b => {
                        if (data.is_wishlisted) {
                            b.classList.add('active');
                            b.innerHTML = '<i class="bi bi-heart-fill"></i>';
                        } else {
                            b.classList.remove('active');
                            b.innerHTML = '<i class="bi bi-heart"></i>';
                        }
                    });

                    // Update Wishlist badge in navbar
                    const badge = document.querySelector('.js-wishlist-badge');
                    if (badge) {
                        badge.textContent = data.wishlist_count;
                        badge.style.display = data.wishlist_count > 0 ? 'inline-block' : 'none';
                    }

                    // If we're on the wishlist page and item was removed, optionally fade out card
                    const wishlistItem = document.querySelector(`.js-wishlist-card[data-event-id="${eventId}"]`);
                    if (wishlistItem && !data.is_wishlisted) {
                        wishlistItem.style.opacity = '0';
                        wishlistItem.style.transform = 'scale(0.95)';
                        setTimeout(() => wishlistItem.remove(), 250);
                    }
                }
            } catch (err) {
                console.error('Error toggling wishlist:', err);
            }
        });
    });

    // Mark Notification as Read (AJAX)
    document.querySelectorAll('.js-mark-notif-read').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const notifId = btn.dataset.notifId;
            const url = `/notifications/${notifId}/read/`;

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    const notifItem = document.querySelector(`.vtx-notification-item[data-notif-id="${notifId}"]`);
                    if (notifItem) {
                        notifItem.classList.remove('unread');
                        btn.remove();
                    }
                    // Update unread count badge
                    const notifBadge = document.querySelector('.js-notif-badge');
                    if (notifBadge) {
                        notifBadge.textContent = data.unread_count;
                        notifBadge.style.display = data.unread_count > 0 ? 'inline-block' : 'none';
                    }
                }
            } catch (err) {
                console.error('Error marking notification read:', err);
            }
        });
    });

    // Mark All Notifications as Read (AJAX)
    const markAllBtn = document.querySelector('.js-mark-all-read');
    if (markAllBtn) {
        markAllBtn.addEventListener('click', async (e) => {
            e.preventDefault();
            try {
                const response = await fetch('/notifications/read-all/', {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrftoken,
                        'X-Requested-With': 'XMLHttpRequest',
                        'Accept': 'application/json'
                    }
                });
                if (response.ok) {
                    document.querySelectorAll('.vtx-notification-item.unread').forEach(item => {
                        item.classList.remove('unread');
                    });
                    document.querySelectorAll('.js-mark-notif-read').forEach(btn => btn.remove());
                    const notifBadge = document.querySelector('.js-notif-badge');
                    if (notifBadge) {
                        notifBadge.style.display = 'none';
                    }
                    markAllBtn.remove();
                }
            } catch (err) {
                console.error('Error marking all notifications read:', err);
            }
        });
    }
});
