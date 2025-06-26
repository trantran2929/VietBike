#backend/Admin/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from backend.models import Ride, User, DriverProfile, Complaint, Notification
from django.db import models
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(300))
    def get(self, request):
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Chỉ admin mới có thể truy cập dashboard.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            total_rides = Ride.objects.count()
            completed_rides = Ride.objects.filter(status='completed').count()
            total_revenue = Ride.objects.filter(status='completed').aggregate(models.Sum('fare'))['fare__sum'] or 0
            active_drivers = DriverProfile.objects.filter(is_available=True, verification_status='approved').count()
            recent_rides = Ride.objects.select_related('user', 'driver__user').order_by('-requested_at')[:5]
            rides_data = []
            for ride in recent_rides:
                start_loc = ride.locations.filter(location_type='start').first()
                end_loc = ride.locations.filter(location_type='end').first()
                if not start_loc or not end_loc:
                    continue
                rides_data.append({
                    'id': ride.id,
                    'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                    'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                    'fare': float(ride.fare),
                    'status': ride.status,
                    'requested_at': ride.requested_at,
                    'customer': ride.user.username,
                    'driver': ride.driver.user.username if ride.driver else None
                })
            return Response({
                'total_rides': total_rides,
                'completed_rides': completed_rides,
                'total_revenue': float(total_revenue),
                'active_drivers': active_drivers,
                'recent_rides': rides_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {str(e)}")
            return Response({'error': 'Lỗi khi tải dữ liệu dashboard.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminUsersView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(300))
    def get(self, request):
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Chỉ admin mới có thể quản lý người dùng.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            users = User.objects.select_related('driverprofile').all()
            users_data = []
            for user in users:
                user_data = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'role': user.role,
                    'created_at': user.created_at
                }
                if user.role == 'driver' and hasattr(user, 'driverprofile'):
                    user_data['driver_info'] = {
                        'license_plate': user.driverprofile.license_plate,
                        'brand': user.driverprofile.brand,
                        'model': user.driverprofile.model,
                        'year': user.driverprofile.year,
                        'vehicle_type': user.driverprofile.vehicle_type,
                        'verification_status': user.driverprofile.verification_status
                    }
                users_data.append(user_data)
            return Response({'users': users_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching users: {str(e)}")
            return Response({'error': 'Lỗi khi tải danh sách người dùng.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AdminRidesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(300))
    def get(self, request):
        user = request.user
        if user.role != 'admin':
            return Response({'error': 'Chỉ admin mới có thể quản lý chuyến đi.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            rides = Ride.objects.select_related('user', 'driver__user')
            rides_data = []
            for ride in rides:
                start_loc = ride.locations.filter(location_type='start').first()
                end_loc = ride.locations.filter(location_type='end').first()
                if not start_loc or not end_loc:
                    continue
                rides_data.append({
                    'id': ride.id,
                    'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                    'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                    'fare': float(ride.fare),
                    'status': ride.status,
                    'requested_at': ride.requested_at,
                    'completed_at': ride.completed_at,
                    'customer': ride.user.username,
                    'driver': ride.driver.user.username if ride.driver else None
                })
            return Response({'rides': rides_data}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching rides: {str(e)}")
            return Response({'error': 'Lỗi khi tải danh sách chuyến đi.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ResolveComplaintView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, complaint_id):
        try:
            complaint = Complaint.objects.get(id=complaint_id)
            new_status = request.data.get('status', 'resolved')  # Đổi tên biến thành new_status
            if new_status not in ['pending', 'resolved']:
                return Response({'error': 'Trạng thái không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
            complaint.status = new_status
            complaint.save()
            if new_status == 'resolved' and complaint.ride:
                Notification.objects.create(
                    user=complaint.user,
                    ride=complaint.ride,
                    message="Khiếu nại của bạn đã được giải quyết."
                )
            logger.info(f"Complaint {complaint.id} updated to {new_status} by admin {request.user.username}")
            return Response({
                'message': 'Khiếu nại đã được xử lý.',
                'complaint': {
                    'id': complaint.id,
                    'ride_id': complaint.ride.id if complaint.ride else None,
                    'status': complaint.status
                }
            }, status=status.HTTP_200_OK)
        except Complaint.DoesNotExist:
            logger.warning(f"Complaint {complaint_id} not found")
            return Response({'error': 'Khiếu nại không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error resolving complaint {complaint_id}: {str(e)}")
            return Response({'error': 'Lỗi khi xử lý khiếu nại.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PendingDriverProfilesView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    @method_decorator(cache_page(300))
    def get(self, request):
        try:
            pending_profiles = DriverProfile.objects.filter(
                verification_status='pending'
            ).select_related('user').values(
                'id',
                'id_number',
                'license_number',
                'license_plate',
                'brand',
                'model',
                'year',
                'vehicle_type',
                'driver_license',
                'vehicle_photo',
                'verification_status',
                'user__username',
                'user__email'
            )
            return Response({
                'message': 'Danh sách hồ sơ tài xế đang chờ duyệt.',
                'profiles': [{
                    'id': profile['id'],
                    'id_number': profile['id_number'],
                    'license_number': profile['license_number'],
                    'license_plate': profile['license_plate'],
                    'brand': profile['brand'],
                    'model': profile['model'],
                    'year': profile['year'],
                    'vehicle_type': profile['vehicle_type'],
                    'driver_license': profile['driver_license'],
                    'vehicle_photo': profile['vehicle_photo'],
                    'verification_status': profile['verification_status'],
                    'username': profile['user__username'],
                    'email': profile['user__email']
                } for profile in pending_profiles]
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error fetching pending driver profiles: {str(e)}")
            return Response({'error': 'Lỗi khi tải danh sách hồ sơ tài xế.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class VerifyDriverView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, driver_id):
        try:
            driver_profile = DriverProfile.objects.select_related('user').get(id=driver_id)
            verification_status = request.data.get('status')
            if verification_status not in ['approved', 'rejected']:
                logger.warning(f"Invalid verification status: {verification_status} for driver_id {driver_id}")
                return Response({'error': 'Trạng thái không hợp lệ. Chọn "approved" hoặc "rejected".'}, status=status.HTTP_400_BAD_REQUEST)

            driver_profile.verification_status = verification_status
            if verification_status == 'approved':
                driver_profile.user.role = 'driver'
                driver_profile.user.save()

            driver_profile.save()
            Notification.objects.create(
                user=driver_profile.user,
                message=f"Hồ sơ tài xế của bạn đã được {verification_status}."
            )
            # Thông báo cho admin
            Notification.objects.create(
                user=request.user,
                message=f"Bạn đã {verification_status} hồ sơ tài xế của {driver_profile.user.username}."
            )
            logger.info(f"Driver {driver_profile.user.username} verification updated to {verification_status} by admin {request.user.username}")

            return Response({
                'message': f'Hồ sơ tài xế đã được {verification_status}.',
                'driver_profile': {
                    'id': driver_profile.id,
                    'id_number': driver_profile.id_number,
                    'license_number': driver_profile.license_number,
                    'license_plate': driver_profile.license_plate,
                    'brand': driver_profile.brand,
                    'model': driver_profile.model,
                    'year': driver_profile.year,
                    'vehicle_type': driver_profile.vehicle_type,
                    'username': driver_profile.user.username,
                    'email': driver_profile.user.email,
                    'verification_status': driver_profile.verification_status
                }
            }, status=status.HTTP_200_OK)
        except DriverProfile.DoesNotExist:
            logger.warning(f"Driver profile {driver_id} not found")
            return Response({'error': 'Hồ sơ tài xế không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error verifying driver profile {driver_id}: {str(e)}")
            return Response({'error': 'Lỗi khi xử lý hồ sơ tài xế.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)