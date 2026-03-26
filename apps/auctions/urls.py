from django.urls import path
from . import views

urlpatterns = [
    path('', views.listing_list, name='listing_list'),
    path('listing/create/', views.listing_create, name='listing_create'),
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('listing/<int:pk>/bids/', views.bid_partial_view, name='bid_partial'),
    path('listing/<int:pk>/update/', views.listing_update, name='listing_update'),
    path('listing/<int:pk>/delete/', views.listing_delete, name='listing_delete'),
    path('listing/<int:pk>/withdraw/', views.listing_withdraw, name='listing_withdraw'),
    path('my-listings/', views.my_listings, name='my_listings'),
]
