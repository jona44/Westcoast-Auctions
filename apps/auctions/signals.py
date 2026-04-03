from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Bid, Listing
from .search import index_listing, remove_listing_from_index

@receiver(post_save, sender=Bid)
def send_bid_update(sender, instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f'listing_{instance.listing.id}',
            {
                'type': 'bid.update'
            }
        )

@receiver(post_save, sender=Listing)
def update_listing_search_index(sender, instance, **kwargs):
    index_listing(instance)

@receiver(post_delete, sender=Listing)
def remove_listing_search_index(sender, instance, **kwargs):
    remove_listing_from_index(instance.id)
