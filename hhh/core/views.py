from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Listing, UpcomingCrop, Crop, User,Bid
from .forms import UpcomingCropForm
from rest_framework.decorators import api_view
from rest_framework.response import Response
import requests
from .models import Listing, BuyerRequest
import requests
from django.http import JsonResponse

@api_view(['GET'])
def get_mandi_price(request):
    crop = request.GET.get("crop", "").strip().title()  # Normalize input

    if not crop:
        return Response({"error": "Crop required"}, status=400)

    API_KEY = "579b464db66ec23bdd000001cdd3946e44ce4aad7209ff7b23ac571b"

    url = "https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070"

    params = {
        "api-key": API_KEY,
        "format": "json",
        "limit": 10,
        "filters[commodity]": crop,   # Filter the crop
    }

    # 🔍 Fetch data from Government API
    try:
        res = requests.get(url, params=params).json()
        print("DEBUG:", res)   # Debug output in terminal

    except Exception as e:
        return Response({"error": "API request failed", "details": str(e)}, status=500)

    # ❌ No crop results
    if not res.get("records"):
        return Response({
            "crop": crop,
            "modal_price_per_kg": None,
            "market": None,
            "district": None,
            "state": None,
        })

    # ✅ First market record
    rec = res["records"][0]

    return Response({
        "crop": crop,
        "market": rec.get("market"),
        "district": rec.get("district"),
        "state": rec.get("state"),
        "modal_price_per_kg": rec.get("modal_price"),
    })

def index(request):
    users_count = User.objects.count()
    return render(request, 'index.html', {'users_count': users_count})


@login_required
def profile(request):
    user = request.user

    # Seller listings
    listings = Listing.objects.filter(seller=user)

    # Requests seller received (incoming)
    buyer_requests = BuyerRequest.objects.filter(
        seller=user
    ).order_by("-created_at")

    # Requests the user sent (outgoing)
    my_requests = BuyerRequest.objects.filter(
        buyer=user
    ).order_by("-created_at")

    # Stats for dashboard
    stats = {
        "total_listings": listings.count(),
        "active_listings": listings.filter(is_active=True).count(),
        "total_requests": buyer_requests.count(),
        "completed_orders": buyer_requests.filter(status="accepted").count(),
        "highest_bid": None,  # not used; kept for compatibility
        "last_listing": listings.order_by("-created_at").first(),
    }

    return render(request, "profile.html", {
        "listings": listings,
        "buyer_requests": buyer_requests,   # seller sees these
        "my_requests": my_requests,         # buyer sees these
        "stats": stats,
    })


# ---------------------------------------------
# AUTHENTICATION
# ---------------------------------------------
def signup(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        phone = request.POST.get("phone")

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, "signup.html")

        user = User.objects.create_user(
            username=username,
            password=password,
            phone=phone,
        )
        auth_login(request, user)  # <-- Django login helper
        return redirect("dashboard")

    return render(request, "signup.html")


def login(request):   # <-- you asked to keep this name
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)  # <-- Django login() safely used
            return redirect("dashboard")
        else:
            return render(request, "login.html",
                          {"error": "Invalid username or password"})

    return render(request, "login.html")


def logout(request):
    return redirect("login")


# ---------------------------------------------
# USER PAGES
# ---------------------------------------------
@login_required
def dashboard(request):
    listings = Listing.objects.filter(is_active=True).order_by('-created_at')[:20]
    return render(request, 'dashboard.html', {'listings': listings})


@login_required
def sell(request):
    crops = Crop.objects.all()
    return render(request, 'sell.html', {'crops': crops})

@login_required
def buy(request):
    listings = Listing.objects.filter(is_active=True)
    return render(request, "buy.html", {"listings": listings})

@login_required
def listing_detail(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    return render(request, 'listing_detail.html', {'listing': listing})


@login_required
def upcoming(request):
    items = UpcomingCrop.objects.order_by('expected_ready_date')[:50]
    return render(request, 'upcoming.html', {'items': items})

@login_required
def upcoming_create(request):
    if request.method == "POST":
        form = UpcomingCropForm(request.POST)
        if form.is_valid():
            upcoming = form.save(commit=False)
            upcoming.seller = request.user
            upcoming.save()
            return redirect("upcoming")
    else:
        form = UpcomingCropForm()

    return render(request, "upcoming_create.html", {"form": form})

def buy(request):
    # Initial queryset (everything)
    listings = Listing.objects.all().select_related("crop", "seller").prefetch_related("images")

    # Optional backend filters (if you want backend filtering too)
    crop = request.GET.get("crop")
    region = request.GET.get("region")
    min_price = request.GET.get("min")
    max_price = request.GET.get("max")
    date = request.GET.get("date")

    # Apply filters if they exist
    if crop:
        listings = listings.filter(crop__name__icontains=crop)

    if region:
        listings = listings.filter(seller__profile__region__iexact=region)

    if min_price:
        listings = listings.filter(price_per_unit__gte=min_price)

    if max_price:
        listings = listings.filter(price_per_unit__lte=max_price)

    if date:
        listings = listings.filter(created_at__date=date)

    context = {
        "listings": listings
    }
    return render(request, "buy.html", context)

@login_required
def accept_request(request, request_id):
    buyer_request = get_object_or_404(BuyerRequest, id=request_id)

    # Only the seller can accept the request
    if buyer_request.seller != request.user:
        messages.error(request, "You are not allowed to accept this request.")
        return redirect("profile")

    # Update request status
    buyer_request.status = "accepted"
    buyer_request.contact_unlocked = True   # unlock seller contact
    buyer_request.save()

    messages.success(request, "You accepted the request. Your contact is now visible to the buyer.")
    return redirect("profile")


@login_required
def send_request(request, listing_id):
    listing = get_object_or_404(Listing, id=listing_id)

    # Buyer cannot request their own listing
    if request.user == listing.seller:
        messages.error(request, "You cannot request your own listing.")
        return redirect('listing_detail', pk=listing_id)

    # Check if the buyer already requested this listing
    existing = BuyerRequest.objects.filter(
        listing=listing,
        buyer=request.user
    ).first()

    if existing:
        messages.info(request, "You already sent a request.")
        return redirect('listing_detail', pk=listing_id)

    # Create a new buyer request
    BuyerRequest.objects.create(
        listing=listing,
        buyer=request.user,
        seller=listing.seller,
        status="pending",
        message="Buyer wants to purchase your crop."
    )

    messages.success(request, "Request sent successfully!")
    return redirect('listing_detail', pk=listing_id)

@login_required
def reject_request(request, request_id):
    buyer_request = get_object_or_404(BuyerRequest, id=request_id)

    if buyer_request.seller != request.user:
        messages.error(request, "You are not allowed to reject this request.")
        return redirect("profile")

    buyer_request.status = "rejected"
    buyer_request.save()

    messages.info(request, "Request rejected.")
    return redirect("profile")

