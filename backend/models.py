from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator

class User(AbstractUser):
    ROLE_CHOICES = [
        ('customer', 'Customer'),
        ('driver', 'Driver'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=30, unique=True)  # Đặt unique=True
    phone = models.CharField(
        max_length=15,
        blank=True,
        validators=[RegexValidator(
            regex=r'^(0[1-9][0-9]{8,9})$',
            message='Số điện thoại không hợp lệ (10-11 số, bắt đầu bằng 0).'
        )]
    )
    profile_picture = models.ImageField(upload_to='profiles/', null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'phone']

    def __str__(self):
        return self.username

class DriverProfile(models.Model):
    VERIFICATION_STATUS = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    VEHICLE_TYPES = (
        ('bike', 'Bike'),
        ('car', 'Car'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='driverprofile')
    id_number = models.CharField(max_length=12, unique=True)
    license_number = models.CharField(max_length=20, unique=True)
    license_plate = models.CharField(max_length=10, unique=True)
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.PositiveIntegerField()
    vehicle_type = models.CharField(max_length=10, choices=VEHICLE_TYPES, default='bike')
    driver_license = models.ImageField(upload_to='driver_licenses/')
    vehicle_photo = models.ImageField(upload_to='vehicle_photos/')
    is_available = models.BooleanField(default=True)
    rating = models.FloatField(default=0.0)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS, default='pending')

    def update_rating(self):
        ratings = self.ratings.all()
        if ratings.exists():
            self.rating = ratings.aggregate(models.Avg('score'))['score__avg']
        else:
            self.rating = 0.0
        self.save()

    def __str__(self):
        return f"{self.user.username} - Driver Profile"

class Ride(models.Model):
    STATUS_CHOICES = (
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rides')
    driver = models.ForeignKey(DriverProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='rides')
    fare = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='requested')
    requested_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    vehicle_type = models.CharField(max_length=10, choices=DriverProfile.VEHICLE_TYPES, default='bike', blank=True, null=True)

    def __str__(self):
        return f"Ride {self.id} - {self.user.username}"

class RideLocation(models.Model):
    LOCATION_TYPES = (
        ('start', 'Start Location'),
        ('end', 'End Location'),
        ('driver', 'Driver Location'),
    )
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='locations', null=True, blank=True)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    location_type = models.CharField(max_length=10, choices=LOCATION_TYPES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.ride and not self.driver:
            raise ValueError("RideLocation must be associated with either a Ride or a Driver.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.location_type} for {'Ride ' + str(self.ride.id) if self.ride else 'Driver ' + str(self.driver.id)}"

class Rating(models.Model):
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='ratings')
    score = models.FloatField(validators=[MinValueValidator(1.0), MaxValueValidator(5.0)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.driver.update_rating()

    def __str__(self):
        return f"Rating {self.score} for Ride {self.ride.id}"

class Payment(models.Model):
    PAYMENT_METHODS = (
        ('cash', 'Cash'),
        ('momo', 'Momo'),
        ('card', 'Credit Card'),
    )
    ride = models.OneToOneField(Ride, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for Ride {self.ride.id} - {self.method}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"

class Complaint(models.Model):
    ride = models.ForeignKey(Ride, on_delete=models.CASCADE, related_name='complaints')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Complaint for Ride {self.ride.id}"