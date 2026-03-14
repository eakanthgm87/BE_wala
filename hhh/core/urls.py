from django.urls import path,include
from . import views
urlpatterns = [
    path('', views.login, name='login'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path("api/mandi-price/", views.get_mandi_price, name="mandi_price"),
    path('sell/', views.sell, name='sell'),
    path("buy/", views.buy, name="buy"),
    path('listing/<int:pk>/', views.listing_detail, name='listing_detail'),
    path('upcoming/', views.upcoming, name='upcoming'),
    path('upcoming/create/', views.upcoming_create, name="upcoming_create"),
     path("api/mandi-price/", views.get_mandi_price, name="mandi_price"),
    path("api/", include("core.api_urls")),
    path("request/accept/<int:req_id>/", views.accept_request, name="accept_request"),
    path("request/<int:listing_id>/", views.send_request, name="send_request"),
    path("request/<int:request_id>/accept/", views.accept_request, name="accept_request"),
    path("request/<int:request_id>/reject/", views.reject_request, name="reject_request"),


]
