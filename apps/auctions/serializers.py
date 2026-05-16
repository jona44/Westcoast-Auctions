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

    category_display = serializers.CharField(source='get_category_display', read_only=True)
    is_watching = serializers.SerializerMethodField()
    deposit_paid = serializers.SerializerMethodField()
    is_paid = serializers.SerializerMethodField()

    class Meta:
        model = Listing
        fields = [
            'id', 'seller', 'seller_name', 'title', 'description', 
            'starting_bid', 'current_bid', 'image', 'category', 'category_display',
            'deposit_required', 'deposit_amount',
            'start_time', 'end_time', 'is_active', 'created_at',
            'additional_images', 'bids', 'bid_count', 'has_started', 'is_expired',
            'is_watching', 'deposit_paid', 'is_paid'
        ]
        read_only_fields = ['seller', 'current_bid', 'created_at']

    def get_is_watching(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from .models import Watchlist
            return Watchlist.objects.filter(user=request.user, listing=obj).exists()
        return False

    def get_deposit_paid(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated and obj.requires_deposit():
            return obj.deposit_paid_by(request.user)
        return False

    def get_is_paid(self, obj):
        return bool(hasattr(obj, 'close_details') and obj.close_details.is_paid)
