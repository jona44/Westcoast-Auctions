from rest_framework import serializers
from .models import Listing, Bid, ListingImage
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image']

class BidSerializer(serializers.ModelSerializer):
    bidder_name = serializers.ReadOnlyField(source='bidder.username')
    
    class Meta:
        model = Bid
        fields = ['id', 'bidder', 'bidder_name', 'amount', 'timestamp']
        read_only_fields = ['bidder', 'timestamp']

class ListingSerializer(serializers.ModelSerializer):
    seller_name = serializers.ReadOnlyField(source='seller.username')
    additional_images = ListingImageSerializer(many=True, read_only=True)
    bids = BidSerializer(many=True, read_only=True)
    bid_count = serializers.IntegerField(source='bids.count', read_only=True)

    class Meta:
        model = Listing
        fields = [
            'id', 'seller', 'seller_name', 'title', 'description', 
            'starting_bid', 'current_bid', 'image', 'category', 
            'start_time', 'end_time', 'is_active', 'created_at',
            'additional_images', 'bids', 'bid_count'
        ]
        read_only_fields = ['seller', 'current_bid', 'created_at']
