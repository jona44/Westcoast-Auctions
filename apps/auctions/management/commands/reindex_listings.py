from django.core.management.base import BaseCommand
from apps.auctions.models import Listing
from apps.auctions.search import index_listing


class Command(BaseCommand):
    help = 'Reindex active listings in MeiliSearch'

    def handle(self, *args, **options):
        listings = Listing.objects.filter(is_active=True)
        count = listings.count()
        self.stdout.write(self.style.SUCCESS(f'Reindexing {count} active listings...'))
        for listing in listings:
            index_listing(listing)
        self.stdout.write(self.style.SUCCESS('Reindex complete.'))
