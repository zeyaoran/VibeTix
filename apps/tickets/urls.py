from django.urls import path
from . import views

app_name = 'tickets'

urlpatterns = [
    path('my-tickets/', views.my_tickets_view, name='my_tickets'),
    path('my-tickets/<str:ticket_code>/', views.ticket_detail_view, name='detail'),
]
