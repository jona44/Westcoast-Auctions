from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.auctions.models import Listing
from apps.auctions.notifications import send_watchlist_ending_soon_push
from datetime import timedelta

class Command(BaseCommand):
    help = 'Notifies users about watchlisted auctions ending soon'

    def handle(self, *args, **options):
        now = timezone.now()
        # Find active listings that end within the next hour, but haven't been notified yet
        ending_soon = Listing.objects.filter(
            is_active=True,
            notified_ending_soon=False,
            end_time__gt=now,
            end_time__lte=now + timedelta(hours=1)
        )

        count = 0
        for listing in ending_soon:
            # Get all users who watchlisted this listing
            watchers = [watch.user for watch in listing.watchlisted_by.all()]
            for user in watchers:
                send_watchlist_ending_soon_push(listing, user)
                
            listing.notified_ending_soon = True
            listing.save()
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Successfully notified users for {count} ending auctions.'))
