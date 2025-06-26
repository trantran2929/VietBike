#backend/User/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from rest_framework_simplejwt.tokens import RefreshToken
import logging
import re
from django.utils import timezone
from backend.models import DriverProfile

User = get_user_model()
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        phone = request.data.get('phone')
        password = request.data.get('password')
        if not all([username, email, phone, password]):
            return Response({'error': 'Vui lòng cung cấp đầy đủ thông tin.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            return Response({'error': 'Email không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^\d{10}$', phone):  # Giả sử VN phone 10 số
            return Response({'error': 'Số điện thoại không hợp lệ (10 số).'}, status=status.HTTP_400_BAD_REQUEST)
        if len(password) < 6:
            return Response({'error': 'Mật khẩu phải có ít nhất 6 ký tự.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(phone=phone).exists():
            return Response({'error': 'Số điện thoại đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            user = User.objects.create_user(
                username=username, email=email, phone=phone, password=password, role='customer'
            )
            refresh = RefreshToken.for_user(user)
            logger.info(f"User {username} registered successfully.")
            return Response({
                'message': 'Đăng ký thành công!',
                'user': {'username': user.username, 'email': user.email, 'phone': user.phone},
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_201_CREATED)
        except ValueError as e:
            logger.error(f"Invalid data: {str(e)}")
            return Response({'error': 'Dữ liệu không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
            from rest_framework_simplejwt.tokens import RefreshToken

            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                logger.info(f"User {request.user.username} logged out.")
            return Response({'message': 'Đăng xuất thành công!'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error logging out: {str(e)}")
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        profile_data = {
            'username': user.username,
            'email': user.email,
            'phone': user.phone,
            'profile_picture': user.profile_picture.url if user.profile_picture else None,
            'created_at': user.created_at.isoformat(),
            'role': user.role
        }
        if user.role == 'driver':
            try:
                driver_profile = user.driverprofile
                profile_data.update({
                    'driver_info': {
                        'license_plate': driver_profile.license_plate,
                        'brand': driver_profile.brand,
                        'model': driver_profile.model,
                        'year': driver_profile.year,
                        'vehicle_type': driver_profile.vehicle_type,
                        'verification_status': driver_profile.verification_status
                    }
                })
            except DriverProfile.DoesNotExist:
                profile_data['driver_info'] = None
        return Response({'user': profile_data}, status=status.HTTP_200_OK)

class UpdateProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        user = request.user
        username = request.data.get('username', user.username)
        phone = request.data.get('phone', user.phone)
        email = request.data.get('email', user.email)
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')
        remove_image = request.data.get('remove_image')

        license_plate = request.data.get('license_plate')
        brand = request.data.get('brand')
        model = request.data.get('model')
        year = request.data.get('year')
        vehicle_type = request.data.get('vehicle_type')

        logger.debug(f"Request data: {request.data}")
        logger.debug(f"Request FILES: {request.FILES}")

        if email != user.email and User.objects.filter(email=email).exists():
            return Response({'error': 'Email đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if phone != user.phone and User.objects.filter(phone=phone).exists():
            return Response({'error': 'Số điện thoại đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        user.username = username
        user.phone = phone
        user.email = email

        if old_password and new_password:
            if not user.check_password(old_password):
                return Response({'error': 'Mật khẩu cũ không đúng.'}, status=status.HTTP_400_BAD_REQUEST)
            user.set_password(new_password)

        if user.role == 'driver':
            try:
                driver_profile = user.driverprofile
                if license_plate:
                    if not re.match(r'^\d{2}[A-Z]{1,2}-\d{4,5}$', license_plate):
                        return Response({'error': 'Biển số xe không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
                    if license_plate != driver_profile.license_plate and DriverProfile.objects.filter(license_plate=license_plate).exists():
                        return Response({'error': 'Biển số xe đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
                    driver_profile.license_plate = license_plate
                if brand:
                    driver_profile.brand = brand
                if model:
                    driver_profile.model = model
                if year:
                    try:
                        year = int(year)
                        if year < 1900 or year > timezone.now().year:
                            return Response({'error': 'Năm sản xuất không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
                        driver_profile.year = year
                    except ValueError:
                        return Response({'error': 'Năm sản xuất phải là số.'}, status=status.HTTP_400_BAD_REQUEST)
                if vehicle_type:
                    if vehicle_type not in ['bike', 'car']:
                        return Response({'error': 'Loại xe không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
                    driver_profile.vehicle_type = vehicle_type
                driver_profile.save()
            except DriverProfile.DoesNotExist:
                return Response({'error': 'Bạn chưa đăng ký hồ sơ tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        if remove_image == 'true' and user.profile_picture:
            if default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
            user.profile_picture = None
        elif 'profile_picture' in request.FILES:
            profile_picture = request.FILES['profile_picture']
            logger.debug(f"Received file: {profile_picture.name}, size: {profile_picture.size}")
            if profile_picture.size > 5 * 1024 * 1024:
                return Response({'error': 'File ảnh quá lớn. Vui lòng chọn file nhỏ hơn 5MB.'}, status=status.HTTP_400_BAD_REQUEST)
            if user.profile_picture and default_storage.exists(user.profile_picture.name):
                default_storage.delete(user.profile_picture.name)
            try:
                user.profile_picture = profile_picture
                user.save()
                logger.debug(f"File saved at: {user.profile_picture.path}")
            except Exception as e:
                logger.error(f"Error saving file: {str(e)}")
                return Response({'error': f'Lỗi lưu file: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            logger.warning("No profile_picture in request.FILES")

        try:
            user.save()
            logger.info(f"Profile updated for user {user.username}")
            profile_data = {
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'profile_picture': user.profile_picture.url if user.profile_picture else None,
                'created_at': user.created_at.isoformat(),
                'role': user.role
            }
            if user.role == 'driver':
                profile_data['driver_info'] = {
                    'license_plate': driver_profile.license_plate,
                    'brand': driver_profile.brand,
                    'model': driver_profile.model,
                    'year': driver_profile.year,
                    'vehicle_type': driver_profile.vehicle_type,
                    'verification_status': driver_profile.verification_status
                }
            return Response({
                'message': 'Cập nhật hồ sơ thành công!',
                'user': profile_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error updating profile: {str(e)}")
            return Response({'error': 'Lỗi khi cập nhật hồ sơ.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not all([old_password, new_password]):
            return Response({'error': 'Vui lòng cung cấp mật khẩu cũ và mới.'}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({'error': 'Mật khẩu cũ không đúng.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user.set_password(new_password)
            user.save()
            logger.info(f"Password changed for user {user.username}")
            return Response({'message': 'Đổi mật khẩu thành công!'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error changing password: {str(e)}")
            return Response({'error': 'Lỗi khi đổi mật khẩu.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class RegisterDriverView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.debug(f"Received payload: {request.data}, FILES: {request.FILES}")
        user = request.user
        # Kiểm tra vai trò
        if user.role == 'driver' or hasattr(user, 'driverprofile'):
            logger.warning(f"User {user.username} already driver or has profile")
            return Response({'error': 'Bạn đã là tài xế hoặc đã gửi yêu cầu.'}, status=status.HTTP_400_BAD_REQUEST)
        if user.role != 'customer':
            logger.warning(f"User {user.username} not customer, role: {user.role}")
            return Response({'error': 'Chỉ khách hàng có thể đăng ký làm tài xế.'}, status=status.HTTP_400_BAD_REQUEST)

        # Lấy dữ liệu từ request.data và request.FILES
        id_number = request.data.get('id_number')
        license_number = request.data.get('license_number')
        license_plate = request.data.get('license_plate')
        brand = request.data.get('brand')
        model = request.data.get('model')
        year = request.data.get('year')
        vehicle_type = request.data.get('vehicle_type', 'bike')  # Mặc định là bike
        driver_license = request.FILES.get('driver_license')
        vehicle_photo = request.FILES.get('vehicle_photo')

        # Kiểm tra các trường bắt buộc
        required_fields = [id_number, license_number, license_plate, brand, model, year, vehicle_type, driver_license]
        if not all(required_fields):
            logger.warning(f"Missing fields: {required_fields}")
            return Response({'error': 'Vui lòng cung cấp đầy đủ thông tin (bao gồm ảnh bằng lái).'}, status=status.HTTP_400_BAD_REQUEST)

        # Kiểm tra trùng lặp
        if DriverProfile.objects.filter(id_number=id_number).exists():
            logger.warning(f"ID number already exists: {id_number}")
            return Response({'error': 'Số CMND/CCCD đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if DriverProfile.objects.filter(license_number=license_number).exists():
            logger.warning(f"License number already exists: {license_number}")
            return Response({'error': 'Số bằng lái đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)
        if DriverProfile.objects.filter(license_plate=license_plate).exists():
            logger.warning(f"License plate already exists: {license_plate}")
            return Response({'error': 'Biển số xe đã được sử dụng.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate định dạng
        if not re.match(r'^\d{9,12}$', id_number):
            logger.warning(f"Invalid ID number: {id_number}")
            return Response({'error': 'Số CMND/CCCD không hợp lệ (9-12 số).'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^\d{12}$', license_number):
            logger.warning(f"Invalid license number: {license_number}")
            return Response({'error': 'Số bằng lái không hợp lệ (12 số).'}, status=status.HTTP_400_BAD_REQUEST)
        if not re.match(r'^\d{2}[A-Z]{1,2}-\d{4,5}$', license_plate):
            logger.warning(f"Invalid license plate: {license_plate}")
            return Response({'error': 'Biển số xe không hợp lệ (ví dụ: 51A-12345).'}, status=status.HTTP_400_BAD_REQUEST)
        if vehicle_type not in ['bike', 'car']:
            logger.warning(f"Invalid vehicle type: {vehicle_type}")
            return Response({'error': 'Loại xe phải là "bike" hoặc "car".'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            year = int(year)
            if year < 1900 or year > timezone.now().year:
                logger.warning(f"Invalid year: {year}")
                return Response({'error': 'Năm sản xuất không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            logger.warning(f"Year not a number: {year}")
            return Response({'error': 'Năm sản xuất phải là số.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate file
        if driver_license.size > 5 * 1024 * 1024 or (vehicle_photo and vehicle_photo.size > 5 * 1024 * 1024):
            logger.warning(f"File size too large: driver_license={driver_license.size}, vehicle_photo={vehicle_photo.size if vehicle_photo else 0}")
            return Response({'error': 'File ảnh quá lớn (tối đa 5MB).'}, status=status.HTTP_400_BAD_REQUEST)
        allowed_types = ['image/jpeg', 'image/png']
        if driver_license.content_type not in allowed_types or (vehicle_photo and vehicle_photo.content_type not in allowed_types):
            logger.warning(f"Invalid file type: driver_license={driver_license.content_type}, vehicle_photo={vehicle_photo.content_type if vehicle_photo else None}")
            return Response({'error': 'File phải là JPG hoặc PNG.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            driver_profile = DriverProfile.objects.create(
                user=user,
                id_number=id_number,
                license_number=license_number,
                license_plate=license_plate,
                brand=brand,
                model=model,
                year=year,
                vehicle_type=vehicle_type,
                driver_license=driver_license,
                vehicle_photo=vehicle_photo,
                verification_status='pending'
            )
            logger.info(f"Driver profile created for user {user.username}, id: {driver_profile.id}")
            return Response({
                'message': 'Yêu cầu đăng ký tài xế đã được gửi. Vui lòng chờ admin duyệt.',
                'driver_profile': {
                    'id': driver_profile.id,
                    'id_number': driver_profile.id_number,
                    'license_number': driver_profile.license_number,
                    'license_plate': driver_profile.license_plate,
                    'verification_status': driver_profile.verification_status
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            logger.error(f"Error creating driver profile: {str(e)}")
            return Response({'error': 'Lỗi khi đăng ký tài xế.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)