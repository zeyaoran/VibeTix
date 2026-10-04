from django.contrib import admin
from .models import TicketCategory, Ticket


@admin.register(TicketCategory)
class TicketCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'available_quota', 'total_quota', 'max_per_order', 'is_active')
    list_filter = ('is_active', 'event')
    search_fields = ('name', 'event__title')


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('ticket_code', 'holder_name', 'holder_email', 'category', 'status', 'created_at')
    list_filter = ('status', 'category__event', 'created_at')
    search_fields = ('ticket_code', 'holder_name', 'holder_email', 'holder_id_number')
    readonly_fields = ('ticket_code', 'qr_code_hash', 'created_at', 'updated_at')
