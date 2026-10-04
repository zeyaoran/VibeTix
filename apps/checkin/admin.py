from django.contrib import admin
from .models import CheckIn


@admin.register(CheckIn)
class CheckInAdmin(admin.ModelAdmin):
    list_display = ('id', 'ticket', 'checked_by', 'gate_name', 'checked_at')
    list_filter = ('gate_name', 'checked_at')
    search_fields = ('ticket__ticket_code', 'checked_by__username', 'gate_name')
    readonly_fields = ('checked_at',)
