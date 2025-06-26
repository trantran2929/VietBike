# backend/urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .User.views import RegisterView, LogoutView, ProfileView, UpdateProfileView, ChangePasswordView, RegisterDriverView
from .Ride.views import (
    RequestRideView, ListRequestedRidesView, AcceptRideView, UpdateRideStatusView, SubmitComplaintView,
    TrackDriverLocationView, RateRideView, RideHistoryView, UpdateDriverLocationView, NotificationView,
    UpdateDriverStatusView, DriverRidesView
)
from .Payment.views import PaymentView
from .Admin.views import AdminDashboardView, AdminUsersView, AdminRidesView, VerifyDriverView, ResolveComplaintView, PendingDriverProfilesView
app_name = 'backend'

urlpatterns = [
    # Authentication
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('users/logout/', LogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/update/', UpdateProfileView.as_view(), name='update_profile'),
    path('password/change/', ChangePasswordView.as_view(), name='change_password'),
    
    # Driver Registration
    path('drivers/register/', RegisterDriverView.as_view(), name='register_driver'),
    
    # Ride Management
    path('rides/request/', RequestRideView.as_view(), name='request_ride'),
    path('rides/requested/', ListRequestedRidesView.as_view(), name='list_requested_rides'),
    path('rides/<int:ride_id>/accept/', AcceptRideView.as_view(), name='accept_ride'),
    path('rides/<int:ride_id>/status/', UpdateRideStatusView.as_view(), name='update_ride_status'),
    path('rides/<int:ride_id>/track/', TrackDriverLocationView.as_view(), name='track_driver_location'),
    path('rides/rate/', RateRideView.as_view(), name='rate_ride'),
    path('rides/history/', RideHistoryView.as_view(), name='ride_history'),
    path('drivers/location/update/', UpdateDriverLocationView.as_view(), name='update_driver_location'),
    path('drivers/status/update/', UpdateDriverStatusView.as_view(), name='update_driver_status'),  # Thêm endpoint
    path('drivers/rides/', DriverRidesView.as_view(), name='driver_rides'),  # Thêm endpoint
    # Payment
    path('payments/process/', PaymentView.as_view(), name='process_payment'),

    # Admin
    path('admin/dashboard/', AdminDashboardView.as_view(), name='admin_dashboard'),
    path('admin/users/', AdminUsersView.as_view(), name='admin_users'),
    path('admin/rides/', AdminRidesView.as_view(), name='admin_rides'),
    path('complaints/submit/', SubmitComplaintView.as_view(), name='submit_complaint'),
    path('complaints/<int:complaint_id>/resolve/', ResolveComplaintView.as_view(), name='resolve_complaint'),
    path('drivers/<int:driver_id>/verify/', VerifyDriverView.as_view(), name='verify_driver'),
    path('drivers/pending/', PendingDriverProfilesView.as_view(), name='pending_driver_profiles'),  # Thêm endpoint mới

    # Notifications
    path('notifications/', NotificationView.as_view(), name='notifications'),
]