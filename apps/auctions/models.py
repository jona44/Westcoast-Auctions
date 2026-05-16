from django.db import models
from django.conf import settings
from django.utils import timezone

class CategoryChoices(models.TextChoices):
    ELECTRONICS = 'electronics', 'Electronics'
    FASHION = 'fashion', 'Fashion'
    HOME_GARDEN = 'home_garden', 'Home & Garden'
    COLLECTIBLES = 'collectibles', 'Collectibles'
    VEHICLES = 'vehicles', 'Vehicles'
    TOYS = 'toys', 'Toys & Hobbies'
    OTHER = 'other', 'Other'

class Listing(models.Model):
    seller = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    description = models.TextField()
    starting_bid = models.DecimalField(max_digits=12, decimal_places=2)
    current_bid = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='listings/', blank=True, null=True)
    category = models.CharField(
        max_length=50,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER
    )
    deposit_required = models.BooleanField(default=False)
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    escrow_hold = models.BooleanField(default=True)
    start_time = models.DateTimeField(default=timezone.now)
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    notified_ending_soon = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    def requires_deposit(self):
        return bool(self.deposit_required and self.deposit_amount and self.deposit_amount > 0)

    def deposit_paid_by(self, user):
        if not self.requires_deposit() or not user.is_authenticated:
            return False
        from apps.payments.models import PaymentRecord
        return PaymentRecord.objects.filter(
            user=user,
            listing=self,
            payment_type='deposit',
            status='completed'
        ).exists()

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                from PIL import Image
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception:
                pass  # Not a valid image; skip resizing

    @property
    def is_expired(self):
        return timezone.now() > self.end_time

    @property
    def has_started(self):
        return timezone.now() >= self.start_time

    @property
    def has_won(self):
        # Determine if a win record exists for this listing
        return hasattr(self, 'close_details') and self.close_details.winner is not None

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.bidder.username} - {self.amount} on {self.listing.title}"

class AuctionClose(models.Model):
    listing = models.OneToOneField(Listing, on_delete=models.CASCADE, related_name='close_details')
    winner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    winning_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True)
    closed_at = models.DateTimeField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Closed: {self.listing.title}"

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='additional_images')
    image = models.ImageField(upload_to='listings/multi/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for {self.listing.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                from PIL import Image
                img = Image.open(self.image.path)
                if img.height > 800 or img.width > 800:
                    output_size = (800, 800)
                    img.thumbnail(output_size)
                    img.save(self.image.path)
            except Exception:
                pass  # Not a valid image; skip resizing

class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='watchlist')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='watchlisted_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'listing')

    def __str__(self):
        return f"{self.user.username} watching {self.listing.title}"
