from rest_framework import serializers
from .models import User, Crop, Listing, ListingImage, Bid, Order, UserReport, UpcomingCrop, SoilTest, Review, MarketPrice

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id','username','phone','is_red_flagged','report_count')

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = ['id', 'image', 'uploaded_at']


class ListingSerializer(serializers.ModelSerializer):
    crop = serializers.PrimaryKeyRelatedField(read_only=True)

    # Custom fields for manual crop creation
    crop_name = serializers.CharField(write_only=True, required=False)
    crop_description = serializers.CharField(write_only=True, required=False)

    # DRF cannot render ListField for images, so use one ImageField input
    # (But backend will still handle multiple files)
    images = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = Listing
        fields = [
            'id',
            'seller',
            'crop',
            'price_per_unit',
            'base_price',
            'details',
            'terms',
            'created_at',
            'crop_name',
            'crop_description',
            'images',      # single field in form (can upload multiple)
        ]

        read_only_fields = ['id', 'seller', 'crop', 'created_at']



class BidSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bid
        fields = '__all__'
        read_only_fields = ('timestamp','status')

class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = '__all__'
        read_only_fields = ('created_at','approved')

class UserReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserReport
        fields = '__all__'
        read_only_fields = ('reporter','created_at')

class UpcomingCropSerializer(serializers.ModelSerializer):
    class Meta:
        model = UpcomingCrop
        fields = '__all__'
        read_only_fields = ('seller','created_at')

class SoilTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = SoilTest
        fields = '__all__'
        read_only_fields = ('user','uploaded_at')

class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'
        read_only_fields = ('reviewer','created_at')

class MarketPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketPrice
        fields = '__all__'
