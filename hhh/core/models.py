from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
User = settings.AUTH_USER_MODEL



class User(AbstractUser):
    phone = models.CharField(max_length=20, blank=True)
    is_red_flagged = models.BooleanField(default=False)
    report_count = models.IntegerField(default=0)

class Crop(models.Model):
    name = models.CharField(max_length=100)
    crop_type = models.CharField(max_length=50)

    def __str__(self):
        return f"{self.name} ({self.crop_type})"

class Listing(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)
    details = models.TextField(blank=True)
    terms = models.TextField(blank=True)
    harvest_status = models.CharField(max_length=20, choices=[('IN_FIELD','in_field'),('HARVESTED','harvested')], default='IN_FIELD')
    crop_info = models.JSONField(default=dict, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    show_phone_by_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    def __str__(self):
        return f"{self.crop} by {self.seller.username}"

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Bid(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='PENDING')
    accepted_terms = models.BooleanField(default=False)

class Order(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE)
    buyer = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='REQUESTED')
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)
    accepted_terms = models.BooleanField(default=False)
    phone_shared = models.BooleanField(default=False)
    location_shared = models.BooleanField(default=False)

class UserReport(models.Model):
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received')
    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class UpcomingCrop(models.Model):
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='upcoming_crops')
    crop = models.ForeignKey(Crop, on_delete=models.SET_NULL, null=True)
    expected_ready_date = models.DateField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SoilTest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ph = models.FloatField(null=True, blank=True)
    nitrogen = models.FloatField(null=True, blank=True)
    phosphorus = models.FloatField(null=True, blank=True)
    potassium = models.FloatField(null=True, blank=True)
    moisture = models.FloatField(null=True, blank=True)
    report_file = models.FileField(upload_to='soil_reports/', null=True, blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

class Review(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField()
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        unique_together = ('listing', 'reviewer')

class MarketPrice(models.Model):
    region = models.CharField(max_length=100)
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    unit = models.CharField(max_length=20, default='kg')
    timestamp = models.DateTimeField(auto_now=True)


class UpcomingCrop(models.Model):
    description = models.TextField()
    expected_ready_date = models.DateField()
    seller = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Upcoming: {self.description[:20]}"
    
class BuyerRequest(models.Model):

    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
    )

    listing = models.ForeignKey(
        "Listing",
        on_delete=models.CASCADE,
        related_name="requests"
    )

    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="purchase_requests"
    )

    seller = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_requests"
    )

    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="pending"
    )

    # Unlock seller contact only when accepted
    contact_unlocked = models.BooleanField(default=False)

    def __str__(self):
        return f"Request from {self.buyer.username} to {self.seller.username}"

