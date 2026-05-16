from django.contrib import admin

from .models import Listing, Bid, ListingImage

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ('listing', 'image', 'created_at')

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ('title', 'seller', 'category', 'starting_bid', 'current_bid', 'is_active', 'end_time')
    list_filter = ('category', 'is_active')
    search_fields = ('title', 'description', 'seller__username')

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('listing', 'bidder', 'amount', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('listing__title', 'bidder__username')
