from django.contrib import admin
from .models import Artist, Venue, Event
from apps.tickets.models import TicketCategory


class TicketCategoryInline(admin.TabularInline):
    model = TicketCategory
    extra = 1
    fields = ('name', 'price', 'total_quota', 'available_quota', 'max_per_order', 'sales_start_time', 'sales_end_time', 'is_active')


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ('name', 'genre', 'instagram_handle', 'created_at')
    search_fields = ('name', 'genre', 'instagram_handle')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Venue)
class VenueAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'province', 'capacity', 'created_at')
    search_fields = ('name', 'city', 'province', 'address')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'venue', 'start_time', 'end_time', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'is_featured', 'venue__city', 'start_time')
    search_fields = ('title', 'venue__name', 'venue__city')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('artists',)
    inlines = [TicketCategoryInline]
    date_hierarchy = 'start_time'
