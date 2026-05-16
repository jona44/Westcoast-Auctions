from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/listings/(?P<listing_id>\w+)/$', consumers.ListingConsumer.as_asgi()),
]
