from rest_framework import routers
from . import api_views
router = routers.DefaultRouter()
router.register(r'listings', api_views.ListingViewSet, basename='listings')
router.register(r'bids', api_views.BidViewSet, basename='bids')
router.register(r'orders', api_views.OrderViewSet, basename='orders')
router.register(r'users/reports', api_views.UserReportViewSet, basename='reports')
router.register(r'upcoming', api_views.UpcomingCropViewSet, basename='upcoming')
router.register(r'soiltests', api_views.SoilTestViewSet, basename='soiltests')
router.register(r'reviews', api_views.ReviewViewSet, basename='reviews')
router.register(r'crops', api_views.CropViewSet, basename='crops')
router.register(r'market', api_views.MarketPriceViewSet, basename='market')
urlpatterns = router.urls
