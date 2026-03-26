from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Listing, Bid, ListingImage, AuctionClose
from .forms import ListingForm, BidForm
from django.utils import timezone

from .notifications import send_outbid_notification, send_win_notification, send_seller_notification

from django.db.models import Q

def listing_list(request):
    query = request.GET.get('q')
    category = request.GET.get('category')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    sort = request.GET.get('sort', 'closing_soon')

    listings = Listing.objects.filter(is_active=True, end_time__gt=timezone.now())

    if query:
        listings = listings.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    
    if category:
        listings = listings.filter(category=category)
        
    if min_price:
        listings = listings.filter(current_bid__gte=min_price)
        
    if max_price:
        listings = listings.filter(current_bid__lte=max_price)

    if sort == 'closing_soon':
        listings = listings.order_by('end_time')
    elif sort == 'newest':
        listings = listings.order_by('-created_at')
    elif sort == 'price_low':
        listings = listings.order_by('current_bid')
    elif sort == 'price_high':
        listings = listings.order_by('-current_bid')

    categories = Listing.objects.values_list('category', flat=True).distinct()

    return render(request, 'auctions/listing_list.html', {
        'listings': listings,
        'categories': categories,
        'search_query': query,
        'selected_category': category,
        'min_price': min_price,
        'max_price': max_price,
        'sort': sort
    })

def bid_partial_view(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    bids = listing.bids.all().order_by('-timestamp')
    return render(request, 'auctions/partials/bid_info.html', {
        'listing': listing,
        'bids': bids,
        'now': timezone.now()
    })

def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    bids = listing.bids.all().order_by('-timestamp')
    
    if request.method == 'POST':
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to place a bid.")
            return redirect('login')
            
        if listing.seller == request.user:
            messages.error(request, "You cannot bid on your own listing.")
            return redirect('listing_detail', pk=pk)
            
        if not listing.has_started:
            messages.error(request, "This auction has not started yet.")
            return redirect('listing_detail', pk=pk)
            
        form = BidForm(request.POST, listing=listing)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.bidder = request.user
            bid.listing = listing
            bid.save()
            
            # Update current bid on listing
            listing.current_bid = bid.amount
            listing.save()
            # Notify previous bidder
            previous_bid = bids.exclude(bidder=request.user).first()
            if previous_bid and previous_bid.bidder != request.user:
                send_outbid_notification(listing, previous_bid.bidder)
                
            messages.success(request, f"Successfully placed bid of ${bid.amount}!")
            return redirect('listing_detail', pk=pk)
    else:
        form = BidForm(listing=listing)

    return render(request, 'auctions/listing_detail.html', {
        'listing': listing,
        'bids': bids,
        'bid_form': form,
        'now': timezone.now()
    })

from apps.moderation.models import ListingApproval

@login_required
def listing_create(request):
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.current_bid = listing.starting_bid
            listing.is_active = False # Require moderation
            listing.save()
            
            # Create Approval record
            ListingApproval.objects.create(listing=listing)
            
            # Save additional images
            images = request.FILES.getlist('additional_images')
            for f in images:
                ListingImage.objects.create(listing=listing, image=f)
                
            messages.success(request, f"Listing '{listing.title}' has been submitted for moderation.")
            return redirect('listing_list') # Redirect to list since it's not visible yet
    else:
        form = ListingForm()
    return render(request, 'auctions/listing_form.html', {'form': form, 'title': 'Create New Auction'})

@login_required
def listing_update(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        messages.error(request, "You are not authorized to edit this listing.")
        return redirect('listing_detail', pk=pk)
        
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.is_active = False # Re-approve on edit
            listing.save()
            
            # Update/Create Approval record
            approval, created = ListingApproval.objects.get_or_create(listing=listing)
            approval.status = 'pending'
            approval.reviewed_at = None
            approval.moderator = None
            approval.rejection_reason = None
            approval.save()
            
            # Save additional images
            images = request.FILES.getlist('additional_images')
            for f in images:
                ListingImage.objects.create(listing=listing, image=f)
                
            messages.success(request, f"Listing '{listing.title}' updated and submitted for re-moderation.")
            return redirect('listing_list')
    else:
        form = ListingForm(instance=listing)
    return render(request, 'auctions/listing_form.html', {'form': form, 'title': 'Update Listing'})

@login_required
def listing_delete(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if listing.seller != request.user:
        messages.error(request, "You are not authorized to delete this listing.")
        return redirect('listing_detail', pk=pk)
        
    if request.method == 'POST':
        listing.delete()
        messages.success(request, "Listing deleted successfully.")
        return redirect('listing_list')
    return render(request, 'auctions/listing_confirm_delete.html', {'listing': listing})


@login_required
def listing_withdraw(request, pk):
    listing = get_object_or_404(Listing, pk=pk)

    # Only the seller can withdraw
    if listing.seller != request.user:
        messages.error(request, "You are not authorized to withdraw this listing.")
        return redirect('listing_detail', pk=pk)

    # Cannot withdraw a listing that is already inactive / withdrawn
    if not listing.is_active:
        messages.error(request, "This listing is already inactive.")
        return redirect('listing_detail', pk=pk)

    bid_count = listing.bids.count()

    if request.method == 'POST':
        if bid_count > 0:
            messages.error(
                request,
                f"Cannot withdraw \"{ listing.title }\": {bid_count} bid(s) have already been placed. "
                "Contact support if you need to cancel a listing with active bids."
            )
            return redirect('listing_withdraw', pk=pk)

        # Deactivate the listing
        listing.is_active = False
        listing.save()
        messages.success(request, f'\"{ listing.title }\" has been successfully withdrawn from sale.')
        return redirect('listing_detail', pk=pk)

    return render(request, 'auctions/listing_confirm_withdraw.html', {
        'listing': listing,
        'bid_count': bid_count,
    })

@login_required
def my_listings(request):
    listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
    return render(request, 'auctions/my_listings.html', {'listings': listings})
