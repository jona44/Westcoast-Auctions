from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Bid
from .serializers import ListingSerializer, BidSerializer
from django.utils import timezone
import django_filters
from django.db.models.functions import Coalesce
from django.db.models import DecimalField

class ListingFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')

    class Meta:
        model = Listing
        fields = ['category']

    def filter_min_price(self, queryset, name, value):
        queryset = queryset.annotate(
            actual_price=Coalesce('current_bid', 'starting_bid', output_field=DecimalField())
        )
        return queryset.filter(actual_price__gte=value)

    def filter_max_price(self, queryset, name, value):
        queryset = queryset.annotate(
            actual_price=Coalesce('current_bid', 'starting_bid', output_field=DecimalField())
        )
        return queryset.filter(actual_price__lte=value)

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ListingFilter
    search_fields = ['title', 'description']
    ordering_fields = ['current_bid', 'end_time', 'created_at']

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def watchlist(self, request):
        listings = Listing.objects.filter(watchlisted_by__user=request.user).order_by('-created_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    def perform_create(self, serializer):
        if not self.request.user.phone_verified:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('Phone verification is required before creating a listing.')

        from apps.moderation.models import ListingApproval
        from .models import ListingImage
        
        listing = serializer.save(
            seller=self.request.user,
            is_active=False, # Require moderation like webapp
            current_bid=serializer.validated_data.get('starting_bid')
        )
        
        # Create Approval record
        ListingApproval.objects.create(listing=listing)
        
        # Save additional images if provided
        images = self.request.FILES.getlist('additional_images')
        for f in images:
            ListingImage.objects.create(listing=listing, image=f)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def place_bid(self, request, pk=None):
        listing = self.get_object()
        
        # Validation
        if listing.seller == request.user:
            return Response({'error': 'You cannot bid on your own listing.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not request.user.phone_verified:
            return Response({'error': 'Phone verification is required before placing a bid.'}, status=status.HTTP_403_FORBIDDEN)

        if listing.deposit_required:
            from apps.payments.models import PaymentRecord
            has_deposit = PaymentRecord.objects.filter(
                user=request.user,
                listing=listing,
                payment_type='deposit',
                status='completed'
            ).exists()
            if not has_deposit:
                return Response(
                    {'error': 'Deposit required before placing bids on this listing.'},
                    status=status.HTTP_402_PAYMENT_REQUIRED
                )

        if not listing.has_started:
            return Response({'error': 'This auction has not started yet.'}, status=status.HTTP_400_BAD_REQUEST)
            
        if timezone.now() > listing.end_time:
            return Response({'error': 'This auction has already ended.'}, status=status.HTTP_400_BAD_REQUEST)

        amount = request.data.get('amount')
        if not amount:
            return Response({'error': 'Amount is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Re-check bid amount vs current bid
        current_amount = listing.current_bid or listing.starting_bid
        if float(amount) <= float(current_amount):
            return Response({'error': f'Bid must be higher than currently highest bid (${current_amount}).'}, status=status.HTTP_400_BAD_REQUEST)

        # Identify the previous highest bidder before saving the new bid
        previous_highest_bid = listing.bids.order_by('-amount').first()
        old_bidder = previous_highest_bid.bidder if previous_highest_bid else None

        # Create bid
        bid = Bid.objects.create(
            listing=listing,
            bidder=request.user,
            amount=amount
        )
        listing.current_bid = amount
        listing.save()

        # In a real app, also trigger notifications here
        from apps.auctions.notifications import send_outbid_push_notification
        
        # If there was a previous bidder and it's not the same person who just bid
        if old_bidder and old_bidder != request.user:
            send_outbid_push_notification(listing, old_bidder, amount)

        return Response(ListingSerializer(listing).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def mine(self, request):
        listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def won(self, request):
        listings = Listing.objects.filter(close_details__winner=request.user).order_by('-close_details__closed_at')
        serializer = self.get_serializer(listings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def toggle_watchlist(self, request, pk=None):
        listing = self.get_object()
        from .models import Watchlist
        watch, created = Watchlist.objects.get_or_create(user=request.user, listing=listing)
        
        if not created:
            # If it already existed, we remove it (toggle off)
            watch.delete()
            return Response({'status': 'removed_from_watchlist', 'is_watching': False})
            
        return Response({'status': 'added_to_watchlist', 'is_watching': True})

class BidViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bid.objects.all().order_by('-timestamp')
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        listing_id = self.request.query_params.get('listing')
        if listing_id:
            return self.queryset.filter(listing_id=listing_id)
        return self.queryset
