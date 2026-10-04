from django.contrib import admin, messages
from .models import Order, OrderItem, Cart, CartItem
from .services import mark_order_as_paid


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('ticket_category', 'quantity', 'unit_price', 'subtotal')


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'grand_total', 'status', 'created_at', 'paid_at')
    list_filter = ('status', 'created_at')
    search_fields = ('order_number', 'user__username', 'user__email')
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    inlines = [OrderItemInline]
    date_hierarchy = 'created_at'
    actions = ['action_mark_as_paid']

    @admin.action(description="Mark selected orders as PAID and generate tickets")
    def action_mark_as_paid(self, request, queryset):
        count = 0
        for order in queryset.filter(status=Order.Status.PENDING):
            mark_order_as_paid(order)
            count += 1
        self.message_user(request, f"Successfully marked {count} order(s) as PAID and generated tickets.", messages.SUCCESS)


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'ticket_category', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('order__order_number', 'ticket_category__name')


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'total_items', 'subtotal', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('id', 'cart', 'ticket_category', 'quantity', 'unit_price', 'subtotal')
    search_fields = ('cart__user__username', 'ticket_category__name')

