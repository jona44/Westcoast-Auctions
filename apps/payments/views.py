from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from apps.auctions.models import Listing, AuctionClose
from .models import PaymentRecord
from .services import generate_payfast_signature, get_payfast_url


@login_required
def checkout_view(request, pk):
    # Final payment for a won auction
    close_info = get_object_or_404(AuctionClose, listing_id=pk)

    if close_info.winner != request.user:
        return HttpResponse("You are not the winner of this auction.", status=403)

    if close_info.is_paid:
        return HttpResponse("This auction has already been paid for.", status=400)

    payfast_data = {
        'merchant_id': settings.PAYFAST_MERCHANT_ID,
        'merchant_key': settings.PAYFAST_MERCHANT_KEY,
        'return_url': settings.PAYFAST_RETURN_URL,
        'cancel_url': settings.PAYFAST_CANCEL_URL,
        'notify_url': settings.PAYFAST_NOTIFY_URL,
        'name_first': request.user.first_name,
        'name_last': request.user.last_name,
        'email_address': request.user.email,
        'm_payment_id': f'FINAL-{close_info.id}-{request.user.id}',
        'amount': str(close_info.winning_bid.amount),
        'item_name': f'Auction Winner: {close_info.listing.title}',
        'custom_str1': 'final',
    }

    payfast_data['signature'] = generate_payfast_signature(payfast_data, settings.PAYFAST_PASSPHRASE)
    payfast_url = get_payfast_url()

    return render(request, 'payments/checkout.html', {
        'payfast_data': payfast_data,
        'payfast_url': payfast_url,
        'close_info': close_info,
        'checkout_type': 'final',
    })


@login_required
def deposit_checkout_view(request, pk):
    # Deposit payment required to bid on a listing
    listing = get_object_or_404(Listing, pk=pk, is_active=True)

    if listing.seller == request.user:
        return HttpResponse("Sellers cannot pay a bid deposit for their own listing.", status=403)

    if not listing.requires_deposit():
        return HttpResponse("This listing does not require a deposit.", status=400)

    if listing.deposit_paid_by(request.user):
        return HttpResponse("Your deposit has already been paid for this listing.", status=400)

    payfast_data = {
        'merchant_id': settings.PAYFAST_MERCHANT_ID,
        'merchant_key': settings.PAYFAST_MERCHANT_KEY,
        'return_url': settings.PAYFAST_RETURN_URL,
        'cancel_url': settings.PAYFAST_CANCEL_URL,
        'notify_url': settings.PAYFAST_NOTIFY_URL,
        'name_first': request.user.first_name,
        'name_last': request.user.last_name,
        'email_address': request.user.email,
        'm_payment_id': f'DEP-{listing.id}-{request.user.id}',
        'amount': str(listing.deposit_amount),
        'item_name': f'Deposit for {listing.title}',
        'custom_str1': 'deposit',
    }

    payfast_data['signature'] = generate_payfast_signature(payfast_data, settings.PAYFAST_PASSPHRASE)
    payfast_url = get_payfast_url()

    return render(request, 'payments/checkout.html', {
        'payfast_data': payfast_data,
        'payfast_url': payfast_url,
        'listing': listing,
        'checkout_type': 'deposit',
    })


@csrf_exempt
def payfast_itn_view(request):
    """
    Handles Instant Transaction Notifications from PayFast.
    """
    if request.method != 'POST':
        return HttpResponse(status=405)

    data = request.POST.dict()
    payment_id = data.get('m_payment_id')
    if not payment_id:
        return HttpResponse(status=400)

    payment_type = 'final'
    if payment_id.startswith('DEP-'):
        payment_type = 'deposit'
        _, listing_id, user_id = payment_id.split('-', 2)
        listing = get_object_or_404(Listing, id=listing_id)
        user = get_user_model().objects.get(id=int(user_id))
    elif payment_id.startswith('FINAL-'):
        payment_type = 'final'
        _, close_id, user_id = payment_id.split('-', 2)
        close_info = get_object_or_404(AuctionClose, id=close_id)
        listing = close_info.listing
        user = close_info.winner
    else:
        return HttpResponse(status=400)

    status_value = 'completed' if data.get('payment_status') == 'COMPLETE' else 'failed'

    PaymentRecord.objects.create(
        user=user,
        listing=listing,
        amount=data.get('amount_gross') or data.get('amount'),
        transaction_id=data.get('pf_payment_id') or data.get('m_payment_id'),
        payment_type=payment_type,
        status=status_value,
    )

    if payment_type == 'final' and status_value == 'completed':
        close_info.is_paid = True
        close_info.save()

    return HttpResponse(status=200)


def payment_success_view(request):
    return render(request, 'payments/success.html')


def payment_cancel_view(request):
    return render(request, 'payments/cancel.html')
