from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from .models import Listing, Bid
from .serializers import ListingSerializer, BidSerializer
from django.utils import timezone

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.filter(is_active=True).order_by('-created_at')
    serializer_class = ListingSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category']
    search_fields = ['title', 'description']
    ordering_fields = ['current_bid', 'end_time', 'created_at']

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def place_bid(self, request, pk=None):
        listing = self.get_object()
        
        # Validation
        if listing.seller == request.user:
            return Response({'error': 'You cannot bid on your own listing.'}, status=status.HTTP_400_BAD_REQUEST)
        
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

        # Create bid
        bid = Bid.objects.create(
            listing=listing,
            bidder=request.user,
            amount=amount
        )
        listing.current_bid = amount
        listing.save()

        # In a real app, also trigger notifications here

        return Response(ListingSerializer(listing).data, status=status.HTTP_201_CREATED)

class BidViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Bid.objects.all().order_by('-timestamp')
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        listing_id = self.request.query_params.get('listing')
        if listing_id:
            return self.queryset.filter(listing_id=listing_id)
        return self.queryset
