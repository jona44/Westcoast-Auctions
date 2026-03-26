from django.core.mail import send_mail
from django.conf import settings

def send_outbid_notification(listing, old_bidder):
    """
    Notifies a bidder they've been outbid.
    """
    subject = f"You've been outbid on '{listing.title}'"
    message = f"Hi {old_bidder.username},\n\nSomeone just placed a higher bid on '{listing.title}'. The new current bid is ${listing.current_bid}.\n\nYou can place a higher bid here: http://localhost:8001/listing/{listing.id}/\n\nGood luck!"
    recipient_list = [old_bidder.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

def send_win_notification(listing, winner):
    """
    Notifies the winning bidder.
    """
    subject = f"Congratulations! You won the auction: '{listing.title}'"
    message = f"Hi {winner.username},\n\nYou are the winner of the auction for '{listing.title}'! Your winning bid was ${listing.current_bid}.\n\nPlease proceed to payment here to secure your item: http://localhost:8001/payments/checkout/{listing.id}/\n\nThank you for bidding!"
    recipient_list = [winner.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)

def send_seller_notification(listing, winner):
    """
    Notifies the seller that their item has been sold.
    """
    seller = listing.seller
    subject = f"Your item '{listing.title}' has been SOLD!"
    if winner:
        message = f"Great news, {seller.username}!\n\nYour item '{listing.title}' was sold for ${listing.current_bid} to {winner.username}.\n\nWe will notify you once the buyer has completed the payment process.\n\nThank you for using Auction Platform!"
    else:
        message = f"Hi {seller.username},\n\nYour auction for '{listing.title}' has ended, but no bids were received.\n\nYou can relist the item here: http://localhost:8001/listing/{listing.id}/update/\n\nBetter luck next time!"
    
    recipient_list = [seller.email]
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipient_list)
