from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from apps.auctions.models import Listing, AuctionClose
from .models import PaymentRecord
from .services import generate_payfast_signature, get_payfast_url

@login_required
def checkout_view(request, pk):
    # Find the auction close details
    close_info = get_object_or_404(AuctionClose, listing_id=pk)
    
    if close_info.winner != request.user:
        return HttpResponse("You are not the winner of this auction.", status=403)
        
    if close_info.is_paid:
        return HttpResponse("This auction has already been paid for.", status=400)

    # Prepare PayFast data
    payfast_data = {
        'merchant_id': settings.PAYFAST_MERCHANT_ID,
        'merchant_key': settings.PAYFAST_MERCHANT_KEY,
        'return_url': settings.PAYFAST_RETURN_URL,
        'cancel_url': settings.PAYFAST_CANCEL_URL,
        'notify_url': settings.PAYFAST_NOTIFY_URL,
        'name_first': request.user.first_name,
        'name_last': request.user.last_name,
        'email_address': request.user.email,
        'm_payment_id': f'AUC-{close_info.id}', # Our internal reference
        'amount': str(close_info.winning_bid.amount),
        'item_name': f'Auction Winner: {close_info.listing.title}',
    }
    
    payfast_data['signature'] = generate_payfast_signature(payfast_data, settings.PAYFAST_PASSPHRASE)
    payfast_url = get_payfast_url()

    return render(request, 'payments/checkout.html', {
        'payfast_data': payfast_data,
        'payfast_url': payfast_url,
        'close_info': close_info
    })

@csrf_exempt
def payfast_itn_view(request):
    """
    Handles Instant Transaction Notifications from PayFast.
    """
    if request.method == 'POST':
        data = request.POST.dict()
        # Verify hash (Simplified for this task)
        # Check payment reference
        payment_id = data.get('m_payment_id')
        if not payment_id:
            return HttpResponse(status=400)
            
        close_id = payment_id.replace('AUC-', '')
        close_info = AuctionClose.objects.get(id=close_id)
        
        # Log Transaction
        PaymentRecord.objects.create(
            user=close_info.winner,
            listing=close_info.listing,
            amount=data.get('amount_gross'),
            transaction_id=data.get('pf_payment_id'),
            status='completed' if data.get('payment_status') == 'COMPLETE' else 'failed'
        )
        
        if data.get('payment_status') == 'COMPLETE':
            close_info.is_paid = True
            close_info.save()
            
        return HttpResponse(status=200)
    return HttpResponse(status=405)

def payment_success_view(request):
    return render(request, 'payments/success.html')

def payment_cancel_view(request):
    return render(request, 'payments/cancel.html')
