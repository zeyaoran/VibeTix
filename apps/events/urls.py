from django.urls import path
from . import views

app_name = 'events'

urlpatterns = [
    path('events/', views.event_list_view, name='list'),
    path('events/<slug:slug>/', views.event_detail_view, name='detail'),
    path('artists/', views.artist_list_view, name='artist_list'),
    path('artists/<slug:slug>/', views.artist_detail_view, name='artist_detail'),
    path('venues/', views.venue_list_view, name='venue_list'),
    path('venues/<slug:slug>/', views.venue_detail_view, name='venue_detail'),
]
