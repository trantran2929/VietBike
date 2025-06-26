#Ride/views.py
from django.db import models
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from backend.models import Ride, DriverProfile, RideLocation, Rating, Notification, Complaint
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
import logging
from math import radians, sin, cos, sqrt, atan2
from django.db import transaction

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RequestRideView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể yêu cầu chuyến.'}, status=status.HTTP_403_FORBIDDEN)
        start_location = request.data.get('start_location')
        end_location = request.data.get('end_location')
        vehicle_type = request.data.get('vehicle_type')
        if not all([start_location, end_location, vehicle_type]):
            return Response({'error': 'Vui lòng cung cấp điểm đi, điểm đến và loại xe.'}, status=status.HTTP_400_BAD_REQUEST)
        if vehicle_type not in ['bike', 'car']:
            return Response({'error': 'Loại xe phải là "bike" hoặc "car".'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            start_lat = float(start_location["latitude"])
            start_lng = float(start_location["longitude"])
            end_lat = float(end_location["latitude"])
            end_lng = float(end_location["longitude"])
            if not (-90 <= start_lat <= 90 and -180 <= start_lng <= 180 and -90 <= end_lat <= 90 and -180 <= end_lng <= 180):
                return Response({'error': 'Tọa độ không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError, KeyError):
            return Response({'error': 'Tọa độ không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        fare = self.calculate_fare(start_lat, start_lng, end_lat, end_lng, vehicle_type)
        ride = Ride.objects.create(
            user=user, fare=fare, vehicle_type=vehicle_type, status='requested'
        )
        RideLocation.objects.create(
            ride=ride, latitude=start_lat, longitude=start_lng, location_type='start'
        )
        RideLocation.objects.create(
            ride=ride, latitude=end_lat, longitude=end_lng, location_type='end'
        )
        Notification.objects.create(
            user=user, ride=ride, message="Yêu cầu chuyến đi của bạn đã được gửi."
        )
        return Response({
            'message': 'Yêu cầu chuyến thành công!',
            'ride': {
                'id': ride.id,
                'start_location': {'lat': start_lat, 'lng': start_lng},
                'end_location': {'lat': end_lat, 'lng': end_lng},
                'fare': float(ride.fare),
                'vehicle_type': ride.vehicle_type,
                'status': ride.status,
                'requested_at': ride.requested_at
            }
        }, status=status.HTTP_201_CREATED)
    def calculate_fare(self, start_lat, start_lng, end_lat, end_lng, vehicle_type):
        R = 6371
        dlat = radians(end_lat - start_lat)
        dlon = radians(end_lng - start_lng)
        a = sin(dlat/2)**2 + cos(radians(start_lat)) * cos(radians(end_lat)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        distance = R * c
        base_fare = 10000 if vehicle_type == 'bike' else 20000
        rate_per_km = 5000
        return round(base_fare + distance * rate_per_km, 2)

class UpdateDriverStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'driver':
            logger.warning(f"User {user.username} not driver, role: {user.role}")
            return Response({'error': 'Chỉ tài xế mới có thể cập nhật trạng thái.'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            driver_profile = user.driverprofile
            if driver_profile.verification_status != 'approved':
                logger.warning(f"Driver {user.username} not approved, status: {driver_profile.verification_status}")
                return Response({'error': 'Hồ sơ tài xế chưa được duyệt.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            logger.warning(f"Driver profile not found for user {user.username}")
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        status_value = request.data.get('status')
        if status_value not in ['active', 'inactive']:
            logger.warning(f"Invalid status: {status_value}")
            return Response({'error': 'Trạng thái không hợp lệ. Chọn "active" hoặc "inactive".'}, status=status.HTTP_400_BAD_REQUEST)

        driver_profile.is_available = (status_value == 'active')
        driver_profile.save()
        logger.info(f"Driver {user.username} updated status to {status_value}")
        
        return Response({
            'message': 'Cập nhật trạng thái tài xế thành công!',
            'status': status_value
        }, status=status.HTTP_200_OK)

class DriverRidesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))
    def get(self, request):
        user = request.user
        if user.role != 'driver':
            logger.warning(f"User {user.username} not driver, role: {user.role}")
            return Response({'error': 'Chỉ tài xế mới có thể xem danh sách chuyến đi.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
            if driver_profile.verification_status != 'approved':
                logger.warning(f"Driver {user.username} not approved, status: {driver_profile.verification_status}")
                return Response({'error': 'Hồ sơ tài xế chưa được duyệt.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            logger.warning(f"Driver profile not found for user {user.username}")
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        rides = Ride.objects.filter(driver=driver_profile).select_related('user')
        rides_data = []
        for ride in rides:
            start_loc = ride.locations.filter(location_type='start').first()
            end_loc = ride.locations.filter(location_type='end').first()
            if not start_loc or not end_loc:
                continue  # Bỏ qua nếu thiếu tọa độ
            ride_data = {
                'id': ride.id,
                'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                'fare': float(ride.fare),
                'status': ride.status,
                'requested_at': ride.requested_at,
                'completed_at': ride.completed_at,
                'customer': ride.user.username
            }
            if ride.status == 'completed':
                try:
                    rating = ride.rating
                    ride_data['rating'] = {
                        'score': rating.score,
                        'comment': rating.comment
                    }
                except AttributeError:
                    ride_data['rating'] = None
            rides_data.append(ride_data)

        return Response({
            'message': 'Danh sách chuyến đi của tài xế.',
            'rides': rides_data
        }, status=status.HTTP_200_OK)

class ListRequestedRidesView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))
    def get(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể xem danh sách chuyến yêu cầu.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
            if not driver_profile.is_available:
                return Response({'error': 'Tài xế hiện không khả dụng.'}, status=status.HTTP_400_BAD_REQUEST)
            if driver_profile.verification_status != 'approved':
                return Response({'error': 'Hồ sơ tài xế chưa được duyệt.'}, status=status.HTTP_400_BAD_REQUEST)
            if not driver_profile.license_plate:
                return Response({'error': 'Vui lòng cập nhật thông tin xe.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            driver_lat = float(request.query_params.get('latitude'))
            driver_lng = float(request.query_params.get('longitude'))
        except (TypeError, ValueError):
            return Response({'error': 'Vui lòng cung cấp tọa độ hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        rides = Ride.objects.filter(status='requested').select_related('user')
        rides_data = []
        for ride in rides:
            start_loc = ride.locations.filter(location_type='start').first()
            if not start_loc:
                continue  # Bỏ qua nếu thiếu tọa độ
            distance = self.calculate_distance(
                (driver_lat, driver_lng),
                (start_loc.latitude, start_loc.longitude)
            )
            if distance <= 5:
                end_loc = ride.locations.filter(location_type='end').first()
                if not end_loc:
                    continue
                rides_data.append({
                    'id': ride.id,
                    'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                    'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                    'fare': float(ride.fare),
                    'distance': round(distance, 2),
                    'requested_at': ride.requested_at,
                    'customer': ride.user.username
                })
        rides_data = sorted(rides_data, key=lambda x: x['distance'])

        return Response({
            'message': 'Danh sách chuyến yêu cầu gần bạn.',
            'rides': rides_data
        }, status=status.HTTP_200_OK)

    def calculate_distance(self, point1, point2):
        lat1, lon1 = point1
        lat2, lon2 = point2
        R = 6371
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        return R * c

class AcceptRideView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request, ride_id):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể chấp nhận chuyến.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            driver_profile = user.driverprofile
            if not driver_profile.is_available or driver_profile.verification_status != 'approved' or not driver_profile.license_plate:
                return Response({'error': 'Tài xế không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            with transaction.atomic():
                ride = Ride.objects.select_for_update().get(id=ride_id, status='requested')
                if driver_profile.rides.filter(status__in=['accepted', 'in_progress']).exists():
                    return Response({'error': 'Bạn đang thực hiện một chuyến khác.'}, status=status.HTTP_400_BAD_REQUEST)
                ride.driver = driver_profile
                ride.status = 'accepted'
                ride.save()
                start_loc = ride.locations.filter(location_type='start').first()
                end_loc = ride.locations.filter(location_type='end').first()
                if not start_loc or not end_loc:
                    return Response({'error': 'Chuyến đi thiếu tọa độ.'}, status=status.HTTP_400_BAD_REQUEST)
                Notification.objects.create(
                    user=ride.user, ride=ride,
                    message=f"Tài xế {user.username} đã chấp nhận chuyến đi của bạn."
                )
                return Response({
                    'message': 'Chấp nhận chuyến thành công!',
                    'ride': {
                        'id': ride.id,
                        'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                        'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                        'fare': float(ride.fare),
                        'status': ride.status,
                        'customer': ride.user.username,
                        'driver': user.username,
                        'license_plate': driver_profile.license_plate
                    }
                }, status=status.HTTP_200_OK)
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc đã được chấp nhận.'}, status=status.HTTP_404_NOT_FOUND)

class UpdateRideStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, ride_id):
        user = request.user
        try:
            ride = Ride.objects.select_related('user', 'driver__user').get(id=ride_id)
        except Ride.DoesNotExist:
            logger.warning(f"Ride {ride_id} not found")
            return Response({'error': 'Chuyến đi không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

        if user.role == 'customer' and ride.user == user:
            ride_status = request.data.get('status')
            if ride_status == 'cancelled' and ride.status not in ['driver_arrived', 'in_progress', 'completed']:
                ride.status = 'cancelled'
                ride.save()
                Notification.objects.create(
                    user=ride.driver.user if ride.driver else user,
                    ride=ride,
                    message="Chuyến đi đã được hủy bởi khách hàng."
                )
                logger.info(f"Ride {ride_id} cancelled by customer {user.username}")
                return Response({
                    'message': 'Chuyến đi đã được hủy.',
                    'ride': {
                        'id': ride.id,
                        'status': ride.status
                    }
                }, status=status.HTTP_200_OK)
            elif ride.status in ['driver_arrived', 'in_progress', 'completed']:
                logger.warning(f"Customer {user.username} attempted to cancel ride {ride_id} in status {ride.status}")
                return Response({'error': 'Không thể hủy chuyến sau khi tài xế đã đến hoặc chuyến đã bắt đầu.'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.warning(f"Customer {user.username} attempted invalid status update: {ride_status}")
                return Response({'error': 'Chỉ tài xế mới có thể cập nhật trạng thái này.'}, status=status.HTTP_403_FORBIDDEN)

        if user.role != 'driver':
            logger.warning(f"User {user.username} not driver, role: {user.role}")
            return Response({'error': 'Chỉ tài xế mới có thể cập nhật trạng thái chuyến.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            driver_profile = user.driverprofile
        except DriverProfile.DoesNotExist:
            logger.warning(f"Driver profile not found for user {user.username}")
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        if ride.driver != driver_profile:
            logger.warning(f"Ride {ride_id} does not belong to driver {user.username}")
            return Response({'error': 'Chuyến đi không thuộc về bạn.'}, status=status.HTTP_403_FORBIDDEN)

        ride_status = request.data.get('status')
        valid_statuses = ['in_progress', 'completed', 'cancelled', 'driver_arrived']
        if ride_status not in valid_statuses:
            logger.warning(f"Invalid status for ride {ride_id}: {ride_status}")
            return Response({'error': f'Trạng thái phải là một trong: {", ".join(valid_statuses)}.'}, status=status.HTTP_400_BAD_REQUEST)

        if ride.status == 'completed' or ride.status == 'cancelled':
            logger.warning(f"Ride {ride_id} already in final status: {ride.status}")
            return Response({'error': 'Chuyến đi đã hoàn thành hoặc bị hủy.'}, status=status.HTTP_400_BAD_REQUEST)

        ride.status = ride_status
        if ride_status == 'completed':
            ride.completed_at = timezone.now()
            driver_profile.is_available = True
            driver_profile.save()
            Notification.objects.create(
                user=ride.user,
                ride=ride,
                message="Chuyến đi của bạn đã hoàn thành."
            )
        ride.save()
        logger.info(f"Ride {ride_id} updated to {ride_status} by driver {user.username}")

        start_loc = ride.locations.filter(location_type='start').first()
        end_loc = ride.locations.filter(location_type='end').first()
        if not start_loc or not end_loc:
            return Response({'error': 'Chuyến đi thiếu tọa độ.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Cập nhật trạng thái chuyến thành công!',
            'ride': {
                'id': ride.id,
                'start_location': {'lat': start_loc.latitude, 'lng': start_loc.longitude},
                'end_location': {'lat': end_loc.latitude, 'lng': end_loc.longitude},
                'fare': float(ride.fare),
                'status': ride.status
            }
        }, status=status.HTTP_200_OK)

class TrackDriverLocationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, ride_id):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể theo dõi vị trí tài xế.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            ride = Ride.objects.select_related('driver').get(id=ride_id, user=user, status__in=['accepted', 'in_progress'])
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)

        if not ride.driver:
            return Response({'error': 'Chuyến đi chưa có tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        latest_location = RideLocation.objects.filter(driver=ride.driver, location_type='driver').order_by('-timestamp').first()
        if not latest_location:
            return Response({'error': 'Không có dữ liệu vị trí hiện tại.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({
            'message': 'Vị trí tài xế hiện tại.',
            'location': {
                'latitude': latest_location.latitude,
                'longitude': latest_location.longitude,
                'timestamp': latest_location.timestamp
            }
        }, status=status.HTTP_200_OK)

class RateRideView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể đánh giá chuyến đi.'}, status=status.HTTP_403_FORBIDDEN)

        ride_id = request.data.get('ride_id')
        score = request.data.get('score')
        comment = request.data.get('comment')

        if not all([ride_id, score]):
            return Response({'error': 'Vui lòng cung cấp ID chuyến đi và điểm đánh giá.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            score = float(score)
            if score < 1 or score > 5:
                return Response({'error': 'Điểm đánh giá phải từ 1 đến 5.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({'error': 'Điểm đánh giá phải là số.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = Ride.objects.select_related('driver').get(id=ride_id, user=user, status='completed')
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại, chưa hoàn thành hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)

        if Rating.objects.filter(ride=ride).exists():
            return Response({'error': 'Chuyến đi này đã được đánh giá.'}, status=status.HTTP_400_BAD_REQUEST)

        rating = Rating.objects.create(
            ride=ride,
            user=user,
            driver=ride.driver,
            score=score,
            comment=comment
        )

        driver_ratings = ride.driver.ratings.all()
        average_rating = driver_ratings.aggregate(models.Avg('score'))['score__avg'] or 0.0
        ride.driver.rating = round(average_rating, 1)
        ride.driver.save()

        Notification.objects.create(
            user=ride.driver.user,
            ride=ride,
            message=f"Bạn nhận được đánh giá {score} sao từ khách hàng {user.username}."
        )

        return Response({
            'message': 'Đánh giá chuyến đi thành công!',
            'rating': {
                'ride_id': ride.id,
                'score': rating.score,
                'comment': rating.comment,
                'created_at': rating.created_at
            }
        }, status=status.HTTP_201_CREATED)

class RideHistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(300))
    def get(self, request):
        user = request.user
        if user.role == 'customer':
            rides = Ride.objects.filter(user=user).select_related('driver__user')
        elif user.role == 'driver':
            rides = Ride.objects.filter(driver=user.driverprofile).select_related('user')
        else:
            return Response({'error': 'Chỉ khách hàng hoặc tài xế mới có thể xem lịch sử chuyến đi.'}, status=status.HTTP_403_FORBIDDEN)

        rides_data = []
        for ride in rides.order_by('-requested_at'):
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

class UpdateDriverLocationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.role != 'driver':
            return Response({'error': 'Chỉ tài xế mới có thể cập nhật vị trí.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            driver_profile = user.driverprofile
            if driver_profile.verification_status != 'approved' or not driver_profile.license_plate:
                return Response({'error': 'Tài xế không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except DriverProfile.DoesNotExist:
            return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            latitude = float(request.data.get('latitude'))
            longitude = float(request.data.get('longitude'))
            if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                return Response({'error': 'Tọa độ không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except (TypeError, ValueError):
            return Response({'error': 'Vui lòng cung cấp tọa độ hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        active_ride = Ride.objects.filter(
            driver=driver_profile, status__in=['accepted', 'in_progress']
        ).first()
        RideLocation.objects.create(
            driver=driver_profile, ride=active_ride, latitude=latitude, longitude=longitude, location_type='driver'
        )
        return Response({'message': 'Cập nhật vị trí thành công!'}, status=status.HTTP_200_OK)

class SubmitComplaintView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể gửi khiếu nại.'}, status=status.HTTP_403_FORBIDDEN)

        ride_id = request.data.get('ride_id')
        description = request.data.get('description')

        if not all([ride_id, description]):
            return Response({'error': 'Vui lòng cung cấp ID chuyến đi và mô tả khiếu nại.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            ride = Ride.objects.get(id=ride_id, user=user)
            complaint = Complaint.objects.create(ride=ride, user=user, description=description)
            Notification.objects.create(
                user=user,
                ride=ride,
                message="Khiếu nại của bạn đã được gửi đến admin."
            )
            logger.info(f"Complaint submitted for ride {ride.id} by user {user.username}")
            return Response({
                'message': 'Gửi khiếu nại thành công!',
                'complaint': {
                    'ride_id': ride.id,
                    'description': complaint.description,
                    'created_at': complaint.created_at
                }
            }, status=status.HTTP_201_CREATED)
        except Ride.DoesNotExist:
            logger.warning(f"Ride {ride_id} not found for user {user.username}")
            return Response({'error': 'Chuyến đi không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error submitting complaint: {str(e)}")
            return Response({'error': 'Lỗi khi gửi khiếu nại.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_page(60))
    def get(self, request):
        notifications = request.user.notifications.filter(is_read=False).select_related('ride').values(
            'id', 'message', 'created_at', 'ride__id'
        )
        return Response({'notifications': list(notifications)}, status=status.HTTP_200_OK)