#backend/admin.py
from django.contrib import admin
from backend.models import User, DriverProfile, Ride, RideLocation, Rating, Payment, Notification, Complaint

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'created_at')
    search_fields = ('username', 'email', 'phone')
    list_filter = ('role', 'created_at')

@admin.register(DriverProfile)
class DriverProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'id_number', 'license_number', 'license_plate', 'verification_status', 'is_available')
    search_fields = ('user__username', 'id_number', 'license_number')
    list_filter = ('verification_status', 'is_available', 'vehicle_type')

@admin.register(Ride)
class RideAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'driver', 'get_start_location', 'get_end_location', 'fare', 'status', 'requested_at')
    search_fields = ('id', 'user__username', 'driver__user__username')
    list_filter = ('status', 'vehicle_type', 'requested_at')

    def get_start_location(self, obj):
        start_loc = obj.locations.filter(location_type='start').first()
        return f"{start_loc.latitude}, {start_loc.longitude}" if start_loc else "N/A"
    get_start_location.short_description = 'Điểm bắt đầu'

    def get_end_location(self, obj):
        end_loc = obj.locations.filter(location_type='end').first()
        return f"{end_loc.latitude}, {end_loc.longitude}" if end_loc else "N/A"
    get_end_location.short_description = 'Điểm kết thúc'

@admin.register(RideLocation)
class RideLocationAdmin(admin.ModelAdmin):
    list_display = ('ride', 'driver', 'latitude', 'longitude', 'location_type', 'timestamp')
    search_fields = ('ride__id', 'driver__user__username')
    list_filter = ('location_type', 'timestamp')

@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('ride', 'user', 'driver', 'score', 'comment', 'created_at')
    search_fields = ('ride__id', 'user__username', 'driver__user__username')
    list_filter = ('score', 'created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('ride', 'amount', 'method', 'status', 'transaction_id', 'created_at')
    search_fields = ('ride__id', 'transaction_id')
    list_filter = ('method', 'status', 'created_at')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'ride', 'message', 'is_read', 'created_at')
    search_fields = ('user__username', 'ride__id', 'message')
    list_filter = ('is_read', 'created_at')

@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('ride', 'user', 'description', 'status', 'created_at')
    search_fields = ('ride__id', 'user__username', 'description')
    list_filter = ('status', 'created_at')