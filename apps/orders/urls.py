from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('orders/', views.order_list_view, name='list'),
    path('orders/<str:order_number>/', views.order_detail_view, name='detail'),
]
