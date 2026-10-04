from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    # Cart URLs
    path('cart/', views.cart_view, name='cart'),
    path('cart/add/<int:category_id>/', views.cart_add_view, name='cart_add'),
    path('cart/update/<int:item_id>/', views.cart_update_view, name='cart_update'),
    path('cart/remove/<int:item_id>/', views.cart_remove_view, name='cart_remove'),
    path('cart/clear/', views.cart_clear_view, name='cart_clear'),

    # Checkout URLs
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/process/', views.checkout_process_view, name='checkout_process'),

    # Order Management URLs
    path('orders/', views.order_list_view, name='list'),
    path('orders/<str:order_number>/', views.order_detail_view, name='detail'),
    path('orders/<str:order_number>/simulate-payment/', views.simulate_payment_view, name='simulate_payment'),
]

