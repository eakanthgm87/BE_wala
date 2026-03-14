from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db.models import F
from .models import User, Crop, Listing, ListingImage, Bid, Order, UserReport, UpcomingCrop, SoilTest, Review, MarketPrice
from .serializers import UserSerializer, CropSerializer, ListingSerializer, ListingImageSerializer, BidSerializer, OrderSerializer, UserReportSerializer, UpcomingCropSerializer, SoilTestSerializer, ReviewSerializer, MarketPriceSerializer

class ListingViewSet(viewsets.ModelViewSet):
    queryset = Listing.objects.all().order_by('-created_at')
    serializer_class = ListingSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def create(self, request, *args, **kwargs):
        data = request.data   # DO NOT COPY

        # Crop fields
        crop_name = data.get("crop_name")
        crop_description = data.get("crop_description", "")

        if not crop_name:
            return Response({"detail": "Crop name is required"}, status=400)

        # Create crop dynamically
        crop = Crop.objects.create(
            name=crop_name,
            crop_type=crop_description
        )

        # Create listing
        listing = Listing.objects.create(
            seller=request.user,
            crop=crop,
            price_per_unit=data.get("price_per_unit"),
            base_price=data.get("base_price"),
            details=data.get("details", ""),
            terms=data.get("terms", "")
        )

        # Multiple images from form
        images = request.FILES.getlist('images')
        for img in images:
            ListingImage.objects.create(listing=listing, image=img)

        # Response
        serializer = ListingSerializer(listing)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def upload_image(self, request, pk=None):
        listing = self.get_object()
        img = request.FILES.get('image')

        if not img:
            return Response({'detail': 'No image provided'}, status=400)

        li = ListingImage.objects.create(listing=listing, image=img)
        return Response(ListingImageSerializer(li).data)




class BidViewSet(viewsets.ModelViewSet):
    queryset = Bid.objects.all().order_by('-timestamp')
    serializer_class = BidSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        listing = get_object_or_404(Listing, pk=data.get('listing'))
        if request.user.is_red_flagged:
            return Response({'detail':'Account restricted'}, status=403)
        amount = float(data.get('amount',0))
        if amount < float(listing.base_price):
            return Response({'detail':'Bid must be >= base price'}, status=400)
        highest = listing.bids.order_by('-amount').first()
        if highest and amount <= float(highest.amount):
            return Response({'detail':'Bid must be higher than current highest'}, status=400)
        data['bidder'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by('-created_at')
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        listing = get_object_or_404(Listing, pk=data.get('listing'))
        if request.user.is_red_flagged:
            return Response({'detail':'Account restricted'}, status=403)
        # require accepted_terms
        if not data.get('accepted_terms'):
            return Response({'detail':'You must accept the seller terms'}, status=400)
        data['buyer'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        order = self.get_object()
        listing = order.listing
        if request.user != listing.seller:
            return Response({'detail':'Only seller can accept'}, status=403)
        share_phone = bool(request.data.get('share_phone', False))
        share_location = bool(request.data.get('share_location', False))
        order.approved = True
        order.phone_shared = share_phone
        order.location_shared = share_location
        order.status = 'ACCEPTED'
        order.save()
        return Response({'detail':'Order accepted'})

class UserReportViewSet(viewsets.ModelViewSet):
    queryset = UserReport.objects.all().order_by('-created_at')
    serializer_class = UserReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        reported_id = data.get('reported_user')
        reported = get_object_or_404(User, pk=reported_id)
        reported.report_count = F('report_count') + 1
        reported.save()
        data['reporter'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # fetch updated
        reported.refresh_from_db()
        if reported.report_count > 5:
            # In a real system, notify admin via email/push; here we just set flag
            reported.is_red_flagged = True
            reported.save()
        return Response(serializer.data, status=201)

class UpcomingCropViewSet(viewsets.ModelViewSet):
    queryset = UpcomingCrop.objects.all().order_by('expected_ready_date')
    serializer_class = UpcomingCropSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(seller=self.request.user)

class SoilTestViewSet(viewsets.ModelViewSet):
    queryset = SoilTest.objects.all().order_by('-uploaded_at')
    serializer_class = SoilTestSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by('-created_at')
    serializer_class = ReviewSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        listing = get_object_or_404(Listing, pk=data.get('listing'))
        # allow only buyers who have completed orders (simplified)
        completed = Order.objects.filter(buyer=request.user, listing=listing, status='COMPLETED').exists()
        if not completed:
            return Response({'detail':'You can only review a listing you bought and completed'}, status=403)
        data['reviewer'] = request.user.id
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    permission_classes = [permissions.AllowAny]

class MarketPriceViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MarketPrice.objects.all().order_by('-timestamp')
    serializer_class = MarketPriceSerializer
    permission_classes = [permissions.AllowAny]
