from django.urls import path, include
from . import views

app_name = 'frontend'  # Namespace cấp cao cho ứng dụng frontend

# URLs cho authentication
auth_patterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register, name='register_user'),  # Đổi name để tránh trùng với driver:register
    path('profile/', views.profile, name='profile'),
]

# URLs cho tài xế
driver_patterns = [
    path('register/', views.register_driver, name='register_driver'),  # Đổi name để tránh trùng
    path('dashboard/', views.driver_dashboard, name='dashboard'),
    path('status/update/', views.update_driver_status, name='update_status'),
    path('rides/list/', views.list_requested_rides, name='list_rides'),
    path('rides/<int:ride_id>/accept/', views.accept_ride, name='accept_ride'),
    path('rides/<int:ride_id>/status/update/', views.update_ride_status, name='update_ride_status'),
]

# URLs cho khách hàng
customer_patterns = [
    path('book/', views.book_ride, name='book_ride'),
    path('history/', views.history, name='history'),
    path('ride/<int:ride_id>/track/', views.track_ride, name='track_ride'),
    path('ride/rate/', views.rate_ride, name='rate_ride'),
    path('payment/process/', views.process_payment, name='payment_process'),
    path('complaint/submit/', views.submit_complaint, name='submit_complaint'),
    # path('payment-and-rating/', views.payment_and_rating, name='payment_and_rating'),  # Thêm URL mới
    path('ride/<int:ride_id>/update-status/', views.update_ride_status, name='update_ride_status'),  # Thêm cho khách hàng
]

# URLs cho admin
admin_patterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('users/', views.admin_users, name='users'),
    path('rides/', views.admin_rides, name='rides'),
    path('drivers/pending/', views.pending_driver_profiles, name='pending_drivers'),
    path('drivers/<int:driver_id>/verify/', views.verify_driver, name='verify_driver'),
    path('complaints/<int:complaint_id>/resolve/', views.resolve_complaint, name='resolve_complaint'),
]

# Kết hợp tất cả patterns
urlpatterns = [
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('auth/', include((auth_patterns, 'auth'), namespace='auth')),
    path('driver/', include((driver_patterns, 'driver'), namespace='driver')),
    path('customer/', include((customer_patterns, 'customer'), namespace='customer')),
    path('admin/', include((admin_patterns, 'admin'), namespace='admin')),
]