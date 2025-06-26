# frontend/views.py
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
import requests
import logging
import re
from django.contrib.auth import logout as django_logout

# Thiết lập logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Base URL của backend API
BACKEND_API_URL = settings.BACKEND_API_URL + '/'

def home(request):
    role = request.session.get('role', '')
    return render(request, 'home.html', {'role': role})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not all([email, password]):
            messages.error(request, 'Vui lòng cung cấp email và mật khẩu.')
            return render(request, 'login.html')

        # Validate email format
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            messages.error(request, 'Email không hợp lệ.')
            return render(request, 'login.html')

        try:
            response = requests.post(BACKEND_API_URL + 'auth/token/', data={
                'email': email,
                'password': password
            })
            if response.status_code == 200:
                data = response.json()
                access_token = data.get('access')
                refresh_token = data.get('refresh')

                # Gọi API profile để lấy thông tin user
                headers = {'Authorization': f'Bearer {access_token}'}
                profile_response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json().get('user')
                    request.session['access_token'] = access_token
                    request.session['refresh_token'] = refresh_token
                    request.session['username'] = profile_data.get('username')
                    request.session['role'] = profile_data.get('role')
                    request.session['driver_profile'] = profile_data.get('driver_profile')
                    request.session.save()

                    logger.info(f"User {profile_data.get('username')} logged in successfully.")
                    return render(request, 'redirect_with_token.html', {
                        'access_token': access_token,
                        'refresh_token': refresh_token,
                        'redirect_url': '/'
                    })
                else:
                    messages.error(request, 'Không thể lấy thông tin hồ sơ.')
            else:
                error = response.json().get('error', 'Email hoặc mật khẩu không đúng.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error during login: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return render(request, 'login.html')
    return render(request, 'login.html')

def logout_view(request):
    if request.method == 'POST':
        refresh_token = request.session.get('refresh_token')
        if refresh_token:
            try:
                headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
                response = requests.post(BACKEND_API_URL + 'users/logout/', data={'refresh': refresh_token}, headers=headers)
                if response.status_code == 200:
                    messages.success(request, 'Đăng xuất thành công!')
                else:
                    messages.error(request, 'Không thể đăng xuất.')
            except requests.RequestException as e:
                logger.error(f"Error during logout: {str(e)}")
                messages.error(request, 'Có lỗi xảy ra khi đăng xuất.')
    
        request.session.flush()
        django_logout(request)
        return redirect('frontend:auth:login')
    return redirect('frontend:auth:login')

def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')

        if not all([username, email, phone, password]):
            messages.error(request, 'Vui lòng cung cấp đầy đủ thông tin.')
            return render(request, 'register.html')

        try:
            response = requests.post(BACKEND_API_URL + 'auth/register/', data={
                'username': username,
                'email': email,
                'phone': phone,
                'password': password
            })
            if response.status_code == 201:
                messages.success(request, 'Đăng ký thành công! Vui lòng đăng nhập.')
                return redirect('frontend:auth:login')
            else:
                error = response.json().get('error', 'Có lỗi xảy ra khi đăng ký.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error during registration: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return render(request, 'register.html')
    return render(request, 'register.html')

def profile(request):
    access_token = request.session.get('access_token')
    if not access_token:
        messages.error(request, 'Vui lòng đăng nhập để xem hồ sơ.')
        return redirect('frontend:auth:login')

    # Gọi API GET /profile/ để lấy thông tin user
    headers = {'Authorization': f'Bearer {access_token}'}
    try:
        response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
        response.raise_for_status()
        profile_data = response.json().get('user', {})
    except requests.RequestException as e:
        logger.error(f"Error fetching profile: {str(e)}")
        messages.error(request, 'Không thể lấy thông tin hồ sơ.')
        profile_data = {}

    if request.method == 'POST':
        if request.POST.get('action') == 'change_password':
            # Đổi mật khẩu (gọi API POST /password/change/)
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')

            try:
                response = requests.post(
                    BACKEND_API_URL + 'password/change/',
                    data={'old_password': old_password, 'new_password': new_password},
                    headers=headers
                )
                response.raise_for_status()
                messages.success(request, 'Đổi mật khẩu thành công!')
            except requests.RequestException as e:
                logger.error(f"Error changing password: {str(e)}")
                try:
                    error = response.json().get('error', 'Có lỗi xảy ra khi đổi mật khẩu.')
                except:
                    error = 'Có lỗi xảy ra khi đổi mật khẩu.'
                messages.error(request, error)
        else:
            # Cập nhật thông tin (gọi API POST /profile/update/)
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            remove_image = request.POST.get('remove_image') == 'true'
            profile_picture = request.FILES.get('profile_picture')

            data = {'email': email, 'phone': phone, 'remove_image': remove_image}
            files = {'profile_picture': profile_picture} if profile_picture else None

            try:
                response = requests.post(
                    BACKEND_API_URL + 'profile/update/',
                    data=data,
                    files=files,
                    headers=headers
                )
                response.raise_for_status()
                messages.success(request, 'Cập nhật hồ sơ thành công!')
                # Cập nhật lại profile_data sau khi update
                profile_data.update({'email': email, 'phone': phone})
                if remove_image:
                    profile_data['profile_picture'] = None
                elif profile_picture:
                    profile_data['profile_picture'] = response.json().get('profile_picture')
            except requests.RequestException as e:
                logger.error(f"Error updating profile: {str(e)}")
                try:
                    error = response.json().get('error', 'Có lỗi xảy ra khi cập nhật hồ sơ.')
                except:
                    error = 'Có lỗi xảy ra khi cập nhật hồ sơ.'
                messages.error(request, error)

        return redirect('frontend:auth:profile')

    return render(request, 'profile.html', {'profile': profile_data})

def register_driver(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để đăng ký tài xế.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể đăng ký làm tài xế.')
        return redirect('frontend:home')

    # Lấy thông tin profile để kiểm tra xem đã có DriverProfile chưa
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    try:
        profile_response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
        if profile_response.status_code == 200:
            profile_data = profile_response.json().get('user')
            if profile_data.get('driver_profile'):
                messages.error(request, 'Bạn đã gửi yêu cầu đăng ký tài xế. Vui lòng chờ admin duyệt.')
                return redirect('frontend:home')
        else:
            messages.error(request, 'Không thể lấy thông tin hồ sơ.')
            return redirect('frontend:auth:login')
    except requests.RequestException as e:
        logger.error(f"Error fetching profile: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:auth:login')

    if request.method == 'POST':
        id_number = request.POST.get('id_number')
        license_number = request.POST.get('license_number')
        license_plate = request.POST.get('license_plate')
        brand = request.POST.get('brand')
        model = request.POST.get('model')
        year = request.POST.get('year')
        vehicle_type = request.POST.get('vehicle_type', 'bike')  # Mặc định là bike nếu không có
        driver_license = request.FILES.get('driver_license')
        vehicle_photo = request.FILES.get('vehicle_photo')

        # Validate dữ liệu trước khi gửi
        if not (id_number and license_number and license_plate and brand and model and year and driver_license):
            messages.error(request, 'Vui lòng điền đầy đủ thông tin.')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Validate id_number (9-12 số)
        if not re.match(r'^\d{9,12}$', id_number):
            messages.error(request, 'Số CMND/CCCD không hợp lệ (9-12 số).')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Validate license_number (12 số)
        if not re.match(r'^\d{12}$', license_number):
            messages.error(request, 'Số bằng lái không hợp lệ (12 số).')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Validate year
        try:
            year = int(year)
            current_year = 2025  # Thời gian hiện tại: 01/06/2025
            if year < 2000 or year > current_year:
                messages.error(request, 'Năm sản xuất không hợp lệ (2000 đến hiện tại).')
                return render(request, 'register_driver.html', {
                    'id_number': id_number,
                    'license_number': license_number,
                    'license_plate': license_plate,
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'vehicle_type': vehicle_type,
                })
        except ValueError:
            messages.error(request, 'Năm sản xuất phải là số hợp lệ.')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Validate license plate format (VD: 92AA-38194)
        if not re.match(r'^[0-9A-Z]{2,4}-[0-9A-Z]{4,6}$', license_plate):
            messages.error(request, 'Biển số xe không hợp lệ (VD: 92AA-38194).')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Validate file
        allowed_types = ['image/jpeg', 'image/png']
        if driver_license.content_type not in allowed_types or (vehicle_photo and vehicle_photo.content_type not in allowed_types):
            messages.error(request, 'File phải là JPG hoặc PNG.')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })
        if driver_license.size > 5 * 1024 * 1024 or (vehicle_photo and vehicle_photo.size > 5 * 1024 * 1024):
            messages.error(request, 'File ảnh quá lớn (tối đa 5MB).')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })

        # Chuẩn bị dữ liệu gửi lên API
        data = {
            'id_number': id_number,
            'license_number': license_number,
            'license_plate': license_plate,
            'brand': brand,
            'model': model,
            'year': year,
            'vehicle_type': vehicle_type,
        }
        files = {
            'driver_license': driver_license,
            'vehicle_photo': vehicle_photo if vehicle_photo else None
        }

        try:
            response = requests.post(BACKEND_API_URL + 'drivers/register/', data=data, files=files, headers=headers)
            if response.status_code == 201:
                # Cập nhật lại session để navbar hiển thị trạng thái "Đang chờ duyệt"
                profile_response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json().get('user')
                    request.session['driver_profile'] = profile_data.get('driver_profile')
                    request.session.save()
                messages.success(request, 'Yêu cầu đăng ký tài xế đã được gửi. Vui lòng chờ admin duyệt.')
                return redirect('frontend:home')
            else:
                error = response.json().get('error', 'Có lỗi xảy ra khi đăng ký tài xế.')
                messages.error(request, error)
                return render(request, 'register_driver.html', {
                    'id_number': id_number,
                    'license_number': license_number,
                    'license_plate': license_plate,
                    'brand': brand,
                    'model': model,
                    'year': year,
                    'vehicle_type': vehicle_type,
                })
        except requests.RequestException as e:
            logger.error(f"Error registering driver: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
            return render(request, 'register_driver.html', {
                'id_number': id_number,
                'license_number': license_number,
                'license_plate': license_plate,
                'brand': brand,
                'model': model,
                'year': year,
                'vehicle_type': vehicle_type,
            })
    return render(request, 'register_driver.html')

def driver_dashboard(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để truy cập dashboard.')
        return redirect('frontend:auth:login')

    # Lấy thông tin profile
    headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
    try:
        profile_response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
        if profile_response.status_code != 200:
            messages.error(request, 'Không thể lấy thông tin hồ sơ.')
            return redirect('frontend:auth:login')
        profile_data = profile_response.json().get('user')
        driver_profile = profile_data.get('driver_profile')
        if not driver_profile or driver_profile.get('verification_status') != 'approved':
            messages.error(request, 'Chỉ tài xế đã được duyệt mới có thể truy cập dashboard.')
            return redirect('frontend:home')

        # Lấy danh sách chuyến đi của tài xế
        rides_response = requests.get(BACKEND_API_URL + 'drivers/rides/', headers=headers)
        rides_data = rides_response.json().get('rides', []) if rides_response.status_code == 200 else []

        # Lấy thông báo
        notifications_response = requests.get(BACKEND_API_URL + 'notifications/', headers=headers)
        notifications = notifications_response.json().get('notifications', []) if notifications_response.status_code == 200 else []

        context = {
            'user': profile_data,
            'rides': rides_data,
            'notifications': notifications
        }
        return render(request, 'driver_dashboard.html', context)
    except requests.RequestException as e:
        logger.error(f"Error fetching driver dashboard: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:auth:login')

def update_driver_status(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để cập nhật trạng thái.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'driver':
        messages.error(request, 'Chỉ tài xế có thể cập nhật trạng thái.')
        return redirect('frontend:home')

    if request.method == 'POST':
        status_value = request.POST.get('status')
        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + 'drivers/status/update/', data={'status': status_value}, headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Cập nhật trạng thái tài xế thành công!')
                return redirect('frontend:driver:dashboard')
            else:
                error = response.json().get('error', 'Có lỗi xảy ra khi cập nhật trạng thái.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error updating driver status: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:driver:dashboard')
    return redirect('frontend:driver:dashboard')

def list_requested_rides(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để xem danh sách chuyến.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'driver':
        messages.error(request, 'Chỉ tài xế có thể xem danh sách chuyến.')
        return redirect('frontend:home')

    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')

    if not latitude or not longitude:
        messages.error(request, 'Vui lòng cung cấp vị trí hiện tại.')
        return render(request, 'list_requested_rides.html')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(
            BACKEND_API_URL + 'rides/requested/',
            params={'latitude': latitude, 'longitude': longitude},
            headers=headers
        )
        if response.status_code == 200:
            rides = response.json().get('rides', [])
            return render(request, 'list_requested_rides.html', {'rides': rides})
        else:
            error = response.json().get('error', 'Không thể lấy danh sách chuyến.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching requested rides: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'list_requested_rides.html')

def accept_ride(request, ride_id):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để chấp nhận chuyến.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'driver':
        messages.error(request, 'Chỉ tài xế có thể chấp nhận chuyến.')
        return redirect('frontend:home')

    if request.method == 'POST':
        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + f'rides/{ride_id}/accept/', headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Chấp nhận chuyến thành công!')
                return redirect('frontend:driver:dashboard')
            else:
                error = response.json().get('error', 'Không thể chấp nhận chuyến.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error accepting ride: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:driver:list_rides')
    return redirect('frontend:driver:list_rides')

def update_ride_status(request, ride_id):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để cập nhật trạng thái chuyến.')
        return redirect('frontend:auth:login')

    role = request.session.get('role')
    if role not in ['driver', 'customer']:
        messages.error(request, 'Chỉ tài xế hoặc khách hàng có thể cập nhật trạng thái chuyến.')
        return redirect('frontend:home')

    if request.method == 'POST':
        status_value = request.POST.get('status')
        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.put(BACKEND_API_URL + f'rides/{ride_id}/status/', data={'status': status_value}, headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Cập nhật trạng thái chuyến thành công!')
                redirect_url = 'frontend:driver:dashboard' if role == 'driver' else 'frontend:customer:history'
                return redirect(redirect_url)
            else:
                error = response.json().get('error', 'Không thể cập nhật trạng thái chuyến.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error updating ride status: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        redirect_url = 'frontend:driver:dashboard' if role == 'driver' else 'frontend:customer:history'
        return redirect(redirect_url)
    return redirect('frontend:home')

def book_ride(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để đặt xe.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể đặt xe.')
        return redirect('frontend:home')

    if request.method == 'POST':
        start_latitude = request.POST.get('start_latitude')
        start_longitude = request.POST.get('start_longitude')
        end_latitude = request.POST.get('end_latitude')
        end_longitude = request.POST.get('end_longitude')
        vehicle_type = request.POST.get('vehicle_type')

        # Validate tọa độ
        try:
            start_lat = float(start_latitude)
            start_lng = float(start_longitude)
            end_lat = float(end_latitude)
            end_lng = float(end_longitude)
            if not (-90 <= start_lat <= 90 and -180 <= start_lng <= 180 and -90 <= end_lat <= 90 and -180 <= end_lng <= 180):
                messages.error(request, 'Tọa độ không hợp lệ.')
                return render(request, 'book_ride.html')
        except (ValueError, TypeError):
            messages.error(request, 'Tọa độ phải là số hợp lệ.')
            return render(request, 'book_ride.html')

        # Validate vehicle_type
        if vehicle_type not in ['bike', 'car']:
            messages.error(request, 'Loại xe phải là "bike" hoặc "car".')
            return render(request, 'book_ride.html')

        data = {
            'start_location': {
                'latitude': start_lat,
                'longitude': start_lng
            },
            'end_location': {
                'latitude': end_lat,
                'longitude': end_lng
            },
            'vehicle_type': vehicle_type
        }

        try:
            headers = {
                'Authorization': f'Bearer {request.session.get("access_token")}',
                'Content-Type': 'application/json'
            }
            response = requests.post(BACKEND_API_URL + 'rides/request/', json=data, headers=headers)
            if response.status_code == 201:
                ride_data = response.json().get('ride')
                messages.success(request, 'Yêu cầu chuyến đi thành công!')
                return redirect('frontend:customer:track_ride', ride_id=ride_data['id'])
            else:
                error = response.json().get('error', 'Không thể đặt chuyến.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error booking ride: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return render(request, 'book_ride.html')
    return render(request, 'book_ride.html')

def track_ride(request, ride_id):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để theo dõi chuyến.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể theo dõi chuyến.')
        return redirect('frontend:home')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        # Lấy thông tin chuyến đi
        ride_response = requests.get(BACKEND_API_URL + f'rides/history/', headers=headers)
        ride = None
        if ride_response.status_code == 200:
            rides = ride_response.json().get('rides', [])
            ride = next((r for r in rides if r['id'] == int(ride_id)), None)
            if not ride:
                messages.error(request, 'Chuyến đi không tồn tại.')
                return render(request, 'track_ride.html')

        # Lấy vị trí tài xế
        response = requests.get(BACKEND_API_URL + f'rides/{ride_id}/track/', headers=headers)
        if response.status_code == 200:
            location_data = response.json().get('location')
            return render(request, 'track_ride.html', {'ride': ride, 'driver_location': location_data})
        else:
            error = response.json().get('error', 'Không thể theo dõi vị trí tài xế.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error tracking ride: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'track_ride.html')

def rate_ride(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để đánh giá chuyến.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể đánh giá chuyến.')
        return redirect('frontend:home')

    if request.method == 'POST':
        ride_id = request.POST.get('ride_id')
        score = request.POST.get('score')
        comment = request.POST.get('comment', '')

        data = {
            'ride_id': ride_id,
            'score': score,
            'comment': comment
        }

        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + 'rides/rate/', data=data, headers=headers)
            if response.status_code == 201:
                messages.success(request, 'Đánh giá chuyến đi thành công!')
                return redirect('frontend:customer:history')
            else:
                error = response.json().get('error', 'Không thể đánh giá chuyến.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error rating ride: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:customer:history')
    return redirect('frontend:customer:history')

def history(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để xem lịch sử.')
        return redirect('frontend:auth:login')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(BACKEND_API_URL + 'rides/history/', headers=headers)
        if response.status_code == 200:
            rides = response.json().get('rides', [])
            return render(request, 'history.html', {'rides': rides})
        else:
            error = response.json().get('error', 'Không thể lấy lịch sử chuyến đi.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching history: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'history.html')

def process_payment(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để thanh toán.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể thanh toán.')
        return redirect('frontend:home')

    if request.method == 'POST':
        ride_id = request.POST.get('ride_id')
        method = request.POST.get('method')
        transaction_id = request.POST.get('transaction_id', '')

        data = {
            'ride_id': ride_id,
            'method': method,
            'transaction_id': transaction_id if method in ['momo', 'card'] else None
        }

        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + 'payments/process/', data=data, headers=headers)
            if response.status_code == 201:
                messages.success(request, 'Thanh toán thành công!')
                return redirect('frontend:customer:history')
            else:
                error = response.json().get('error', 'Không thể xử lý thanh toán.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error processing payment: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:customer:history')
    return redirect('frontend:customer:history')

def submit_complaint(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để gửi khiếu nại.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'customer':
        messages.error(request, 'Chỉ khách hàng có thể gửi khiếu nại.')
        return redirect('frontend:home')

    if request.method == 'POST':
        ride_id = request.POST.get('ride_id')
        description = request.POST.get('description')

        data = {
            'ride_id': ride_id,
            'description': description
        }

        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + 'complaints/submit/', data=data, headers=headers)
            if response.status_code == 201:
                messages.success(request, 'Gửi khiếu nại thành công!')
                return redirect('frontend:customer:history')
            else:
                error = response.json().get('error', 'Không thể gửi khiếu nại.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error submitting complaint: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:customer:history')
    return redirect('frontend:customer:history')

def admin_dashboard(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để truy cập dashboard.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể truy cập dashboard.')
        return redirect('frontend:home')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(BACKEND_API_URL + 'admin/dashboard/', headers=headers)
        if response.status_code == 200:
            dashboard_data = response.json()
            return render(request, 'admin_dashboard.html', dashboard_data)
        else:
            error = response.json().get('error', 'Không thể lấy dữ liệu dashboard.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching admin dashboard: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'admin_dashboard.html')

def admin_users(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để quản lý người dùng.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể quản lý người dùng.')
        return redirect('frontend:home')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(BACKEND_API_URL + 'admin/users/', headers=headers)
        if response.status_code == 200:
            users_data = response.json().get('users', [])
            return render(request, 'admin_users.html', {'users': users_data})
        else:
            error = response.json().get('error', 'Không thể lấy danh sách người dùng.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching admin users: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'admin_users.html')

def admin_rides(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để quản lý chuyến đi.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể quản lý chuyến đi.')
        return redirect('frontend:home')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(BACKEND_API_URL + 'admin/rides/', headers=headers)
        if response.status_code == 200:
            rides_data = response.json().get('rides', [])
            return render(request, 'admin_rides.html', {'rides': rides_data})
        else:
            error = response.json().get('error', 'Không thể lấy danh sách chuyến đi.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching admin rides: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'admin_rides.html')

def verify_driver(request, driver_id):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để duyệt hồ sơ tài xế.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể duyệt hồ sơ tài xế.')
        return redirect('frontend:home')

    if request.method == 'POST':
        status_value = request.POST.get('status')
        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + f'drivers/{driver_id}/verify/', data={'status': status_value}, headers=headers)
            if response.status_code == 200:
                # Cập nhật lại session để navbar phản ánh thay đổi
                profile_response = requests.get(BACKEND_API_URL + 'profile/', headers=headers)
                if profile_response.status_code == 200:
                    profile_data = profile_response.json().get('user')
                    request.session['driver_profile'] = profile_data.get('driver_profile')
                    request.session['role'] = profile_data.get('role')
                    request.session.save()

                messages.success(request, 'Duyệt hồ sơ tài xế thành công!')
                return redirect('frontend:admin:pending_drivers')
            else:
                error = response.json().get('error', 'Không thể duyệt hồ sơ tài xế.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error verifying driver: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:admin:pending_drivers')
    return redirect('frontend:admin:pending_drivers')

def pending_driver_profiles(request):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để xem hồ sơ tài xế đang chờ duyệt.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể xem hồ sơ tài xế đang chờ duyệt.')
        return redirect('frontend:home')

    try:
        headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
        response = requests.get(BACKEND_API_URL + 'drivers/pending/', headers=headers)
        if response.status_code == 200:
            profiles = response.json().get('profiles', [])
            return render(request, 'pending_driver_profiles.html', {'profiles': profiles})
        else:
            error = response.json().get('error', 'Không thể lấy danh sách hồ sơ.')
            messages.error(request, error)
    except requests.RequestException as e:
        logger.error(f"Error fetching pending driver profiles: {str(e)}")
        messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
    return render(request, 'pending_driver_profiles.html')

def resolve_complaint(request, complaint_id):
    if not request.session.get('access_token'):
        messages.error(request, 'Vui lòng đăng nhập để giải quyết khiếu nại.')
        return redirect('frontend:auth:login')

    if request.session.get('role') != 'admin':
        messages.error(request, 'Chỉ admin có thể giải quyết khiếu nại.')
        return redirect('frontend:home')

    if request.method == 'POST':
        status_value = request.POST.get('status')
        try:
            headers = {'Authorization': f'Bearer {request.session.get("access_token")}'}
            response = requests.post(BACKEND_API_URL + f'complaints/{complaint_id}/resolve/', data={'status': status_value}, headers=headers)
            if response.status_code == 200:
                messages.success(request, 'Giải quyết khiếu nại thành công!')
                return redirect('frontend:admin:dashboard')  # Có thể tạo trang quản lý khiếu nại nếu cần
            else:
                error = response.json().get('error', 'Không thể giải quyết khiếu nại.')
                messages.error(request, error)
        except requests.RequestException as e:
            logger.error(f"Error resolving complaint: {str(e)}")
            messages.error(request, 'Có lỗi xảy ra khi kết nối đến server.')
        return redirect('frontend:admin:dashboard')
    return redirect('frontend:admin:dashboard')

def about(request):
    return render(request, 'about.html')

