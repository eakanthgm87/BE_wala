from django.contrib import admin
from .models import User, Crop, Listing, ListingImage, Bid, Order, UserReport, UpcomingCrop, SoilTest, Review, MarketPrice
admin.site.register(User)
admin.site.register(Crop)
admin.site.register(Listing)
admin.site.register(ListingImage)
admin.site.register(Bid)
admin.site.register(Order)
admin.site.register(UserReport)
admin.site.register(UpcomingCrop)
admin.site.register(SoilTest)
admin.site.register(Review)
admin.site.register(MarketPrice)
