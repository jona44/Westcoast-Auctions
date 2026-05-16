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

import firebase_admin
from firebase_admin import credentials, messaging
from apps.accounts.models import FCMDevice
import logging

logger = logging.getLogger(__name__)

# Initialize Firebase app only if it's not already initialized
try:
    if not firebase_admin._apps:
        # Use a real service account file in production
        # cred = credentials.Certificate("firebase-adminsdk.json")
        # firebase_admin.initialize_app(cred)
        pass # To avoid crashing locally if key is missing, leaving pass.
except Exception as e:
    logger.error(f"Failed to initialize Firebase Admin: {e}")

def send_push_notification(user, title, body, data=None):
    """
    Sends an FCM push notification to all registered devices of a given user.
    """
    if not firebase_admin._apps:
        logger.warning(f"Simulating push notification to {user}: Title='{title}', Body='{body}'")
        return
        
    devices = FCMDevice.objects.filter(user=user)
    if not devices.exists():
        return

    tokens = list(devices.values_list('token', flat=True))
    
    # We create a MulticastMessage for multiple device tokens
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        data=data or {},
        tokens=tokens,
    )
    
    try:
        response = messaging.send_each_for_multicast(message)
        logger.info(f"Successfully sent {response.success_count} messages, {response.failure_count} failed")
        
        # Optionally clean up invalid tokens
        if response.failure_count > 0:
            for idx, resp in enumerate(response.responses):
                if not resp.success:
                    if resp.exception.code in ['messaging/invalid-registration-token', 'messaging/registration-token-not-registered']:
                        invalid_token = tokens[idx]
                        FCMDevice.objects.filter(token=invalid_token).delete()
    except Exception as e:
        logger.error(f"Error sending FCM message: {e}")

def send_outbid_push_notification(listing, old_bidder, new_bid_amount):
    """
    Notifies a user they have been outbid via push notification.
    """
    if not old_bidder:
        return
        
    title = f"Outbid on {listing.title}!"
    body = f"Someone placed a higher bid of ${new_bid_amount}. Place another bid now to win!"
    data = {
        'listing_id': str(listing.id),
        'click_action': 'FLUTTER_NOTIFICATION_CLICK' # Often required for routing if needed
    }
    send_push_notification(old_bidder, title, body, data)

def send_watchlist_ending_soon_push(listing, user):
    """
    Notifies a user that an auction they follow is ending soon.
    """
    title = f"Auction Ending Soon!"
    body = f"The auction for '{listing.title}' is ending in less than an hour."
    data = {
        'listing_id': str(listing.id)
    }
    send_push_notification(user, title, body, data)
