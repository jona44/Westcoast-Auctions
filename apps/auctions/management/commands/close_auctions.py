from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.auctions.models import Listing, AuctionClose
from apps.auctions.notifications import send_win_notification, send_seller_notification

class Command(BaseCommand):
    help = 'Finds expired auctions and determines winners'

    def handle(self, *args, **options):
        now = timezone.now()
        expired_listings = Listing.objects.filter(is_active=True, end_time__lte=now)

        if not expired_listings.exists():
            self.stdout.write(self.style.SUCCESS('No auctions to close at this time.'))
            return

        for listing in expired_listings:
            listing.is_active = False
            listing.save()

            # Find the highest bid
            highest_bid = listing.bids.all().order_by('-amount').first()
            
            # Create AuctionClose record
            close_info = AuctionClose.objects.create(
                listing=listing,
                winner=highest_bid.bidder if highest_bid else None,
                winning_bid=highest_bid,
                is_paid=False
            )

            # --- Trigger Notifications ---
            if highest_bid:
                # Notify Winner
                send_win_notification(listing, highest_bid.bidder)
                # Notify Seller about the sale
                send_seller_notification(listing, highest_bid.bidder)
            else:
                # Notify Seller the item didn't sell
                send_seller_notification(listing, None)
            # -----------------------------

            if highest_bid:
                self.stdout.write(self.style.SUCCESS(
                    f'Closed "{listing.title}": Winner is {highest_bid.bidder.username} (${highest_bid.amount})'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'Closed "{listing.title}": No bids received.'
                ))

        self.stdout.write(self.style.SUCCESS(f'Successfully closed {expired_listings.count()} auctions.'))
