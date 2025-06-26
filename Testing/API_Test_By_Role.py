# %%
"""
# API Testing Documentation By Role

Notebook này chứa test cases cho API của hệ thống đặt xe máy, được tổ chức theo từng role (Customer, Driver, Admin) và luồng nghiệp vụ.

## Setup và Cấu hình chung
"""

# %%
import requests
import json

BASE_URL = "http://127.0.0.1:8010/api"
headers = {"Content-Type": "application/json"}

def print_response(response):
    print(f"Status Code: {response.status_code}")
    try:
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
    except:
        print(response.text)

# %%
"""
# 1. Customer Flow

"""

# %%
"""
## 1.1 Customer Authentication Flow

Luồng xử lý cho khách hàng:
1. Đăng ký tài khoản
2. Đăng nhập
3. Làm mới token
4. Đăng xuất
"""

# %%
"""
### 1.1.1 Đăng ký khách hàng
"""

# %%
# Customer Registration
register_endpoint = f"{BASE_URL}/auth/register/"
payload = {
    "username": "customer1",
    "email": "customer@example.com",
    "phone": "0987654321",
    "password": "123456",
    "role": "customer"
}

try:
    response = requests.post(register_endpoint, json=payload)
    response.raise_for_status()
    print_response(response)
    print("Customer registered successfully.")
except requests.exceptions.RequestException as e:
    print("Register Customer Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

# %%
"""
### 1.1.2 Đăng nhập khách hàng
"""

# %%
# Login Customer
login_endpoint = f"{BASE_URL}/auth/token/"
payload = {
    "email": "customer@example.com",
    "password": "123456"
}

try:
    response = requests.post(login_endpoint, json=payload)
    response.raise_for_status()
    # print("Login Customer:", response.status_code, response.json())
    print_response(response)
    # Lưu token cho các request sau này
    access_token = response.json().get('access')
    headers['Authorization'] = f'Bearer {access_token}'
except requests.exceptions.RequestException as e:
    print("Login Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

# %%
"""
## 1.2 Customer Booking Flow

Luồng đặt xe của khách hàng:
1. Tạo yêu cầu chuyến đi mới
2. Theo dõi vị trí tài xế
3. Xem thông tin chuyến đi
4. Thanh toán
5. Đánh giá tài xế
"""

# %%
# Request New Ride
request_ride_endpoint = f"{BASE_URL}/rides/request/"
payload = {
    "start_location": {"latitude": 16.0611, "longitude": 108.2278},
    "end_location": {"latitude": 16.0620, "longitude": 108.2300},
    "vehicle_type": "bike"  # or "car"
}

try:
    response = requests.post(request_ride_endpoint, json=payload, headers=headers)
    response.raise_for_status()
    print("Request Ride:", response.status_code, response.json())
    ride_id = response.json().get('ride').get('id')  # Lưu lại ride_id cho các bước tiếp theo
    print("Ride ID:", ride_id)
except requests.exceptions.RequestException as e:
    print("Request Ride Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")


# %%
# Track Driver Location
if 'ride_id' in locals():
    track_endpoint = f"{BASE_URL}/rides/{ride_id}/track/"

    try:
        response = requests.get(track_endpoint, headers=headers)
        response.raise_for_status()
        print("Track Driver:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Track Driver Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No ride_id available. Please request a ride first.")

# %%
# 3. Get Ride Details
url = f"{BASE_URL}/rides/{ride_id}"
response = requests.get(url, headers=tokens.get_headers('customer'))
print("\nRide Details Response:")
print_response(response)

# %%
# Process Payment
if 'ride_id' in locals():
    payment_endpoint = f"{BASE_URL}/payments/process/"
    payload = {
        "ride_id": ride_id,
        "method": "momo",  # or "cash", "card"
        "transaction_id": "MOMO123456"  # Optional, required for momo/card
    }

    try:
        response = requests.post(payment_endpoint, json=payload, headers=headers)
        response.raise_for_status()
        print("Payment:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Payment Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No ride_id available. Please request a ride first.")

# %%
import requests
from tokens import tokensequest
from validate import validate_response

# Booking Flow Helper Functions
def request_ride(start_lat, start_lng, end_lat, end_lng, fare):
    """Request a new ride with error handling"""
    url = f"{BASE_URL}/rides/request"
    data = {
        "start_location": {"latitude": start_lat, "longitude": start_lng},
        "end_location": {"latitude": end_lat, "longitude": end_lng},
        "fare": fare
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            headers=tokens.get_headers('customer')
        )
        result = validate_response(response, 201)  # Expect 201 Created
        print("\nRide request successful!")
        return result["ride_id"]
    except Exception as e:
        print(f"Failed to request ride: {str(e)}")
        return None

def track_ride(ride_id):
    """Track driver location for a specific ride"""
    url = f"{BASE_URL}/rides/{ride_id}/track"
    try:
        response = requests.get(url, headers=tokens.get_headers('customer'))
        return validate_response(response)
    except Exception as e:
        print(f"Failed to track ride: {str(e)}")
        return None

def process_payment(ride_id, amount, method='momo'):
    """Process ride payment"""
    url = f"{BASE_URL}/payments/process"
    data = {
        "ride_id": ride_id,
        "method": method,
        "amount": amount
    }
    
    try:
        response = requests.post(
            url,
            json=data,
            headers=tokens.get_headers('customer')
        )
        return validate_response(response)
    except Exception as e:
        print(f"Payment failed: {str(e)}")
        return None

# Test the complete booking flow
print("\nTesting complete booking flow...")

# 1. Request ride
ride_id = request_ride(
    start_lat=16.0611,
    start_lng=108.2278,
    end_lat=16.0620,
    end_lng=108.2300,
    fare=100.00
)

if ride_id:
    # 2. Track driver location
    print("\nTracking driver location...")
    location = track_ride(ride_id)
    print_response(response)
    
    # 3. Process payment
    print("\nProcessing payment...")
    payment = process_payment(ride_id, 100.00)
    print_response(response)
    
    # 4. Rate driver
    print("\nRating driver...")
    url = f"{BASE_URL}rides/rate/"
    data = {
        "ride_id": ride_id,
        "score": 4.5,
        "comment": "Tài xế thân thiện và chuyến đi an toàn!"
    }
    response = requests.post(
        url,
        json=data,
        headers=tokens.get_headers('customer')
    )
    print_response(response)

# %%
"""
# 2. Driver Flow
"""

# %%
"""
## 2.1 Driver Registration Flow

Luồng xử lý cho tài xế:
1. Đăng ký tài khoản customer
2. Đăng nhập với tài khoản customer
3. Đăng ký làm tài xế (submit thông tin bổ sung)
4. Chờ xác minh từ Admin
"""

# %%
# 1. Register as Customer first (required to become a driver)
register_endpoint = f"{BASE_URL}/auth/register/"
payload = {
    "username": "driver",
    "email": "driver@example.com",
    "phone": "0987654323",
    "password": "123456"
}

try:
    response = requests.post(register_endpoint, json=payload)
    response.raise_for_status()
    print("Register Driver Account:", response.status_code, response.json())
except requests.exceptions.RequestException as e:
    print("Register Driver Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")


# %%
# 2. Login as driver
login_endpoint = f"{BASE_URL}/auth/token/"
payload = {
    "email": "driver@example.com",
    "password": "123456"
}

try:
    response = requests.post(login_endpoint, json=payload)
    response.raise_for_status()
    print_response(response)
    
    # Lưu token cho các request sau này
    driver_token = response.json().get('access')
    driver_headers = headers.copy()
    driver_headers['Authorization'] = f'Bearer {driver_token}'
except requests.exceptions.RequestException as e:
    print("Login Driver Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

# %%
# 3. Submit Driver License Info
driver_register_endpoint = f"{BASE_URL}/drivers/register/"
payload = {
    "id_number": "123456789012",
    "license_number": "123456789012",
    "license_plate": "43K-99999", 
    "brand": "Honda",
    "model": "Wave",
    "year": 2020,
    "vehicle_type": "bike",
    "driver_license": "dummy_driver_license.jpg",  # Giả lập file
    "vehicle_photo": "dummy_vehicle_photo.jpg"    # Giả lập file
}
try:
    response = requests.post(driver_register_endpoint, json=payload, headers=driver_headers)
    response.raise_for_status()
    print("Submit Driver License Info:", response.status_code)
    print_response(response)
    driver_id = response.json().get('driver_profile', {}).get('id')
    if not driver_id:
        raise ValueError("Không lấy được driver_id từ response")
except requests.exceptions.RequestException as e:
    print("Submit Driver License Error:", response.status_code if 'response' in locals() else 'N/A')
    if 'response' in locals():
        print_response(response)
    print(f"Exception: {str(e)}")

# %%
# Test Driver Rides
driver_rides_endpoint = f"{BASE_URL}/drivers/rides/"
try:
    response = requests.get(driver_rides_endpoint, headers=driver_headers)
    response.raise_for_status()
    print("Driver Rides:", response.status_code)
    print_response(response)
except requests.exceptions.RequestException as e:
    print("Driver Rides Error:", response.status_code if 'response' in locals() else 'N/A')
    if 'response' in locals():
        print_response(response)
    print(f"Exception: {str(e)}")

# %%
"""
## 2.2 Driver Ride Management Flow

Luồng xử lý chuyến đi của tài xế:
1. Cập nhật trạng thái hoạt động
2. Cập nhật vị trí
3. Xem các yêu cầu chuyến đi
4. Chấp nhận chuyến đi
5. Cập nhật trạng thái chuyến đi
"""

# %%
# Update Driver Status
if 'driver_headers' in locals():
    status_endpoint = f"{BASE_URL}/drivers/status/update/"
    payload = {"status": "active"}

    try:
        response = requests.post(status_endpoint, json=payload, headers=driver_headers)
        response.raise_for_status()
        print("Update Status:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Update Status Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

# %%
# Test List Requested Rides
list_rides_endpoint = f"{BASE_URL}/rides/requested/"
params = {
    "latitude": 16.0611,  # Tọa độ Đà Nẵng
    "longitude": 108.2278
}
try:
    response = requests.get(list_rides_endpoint, params=params, headers=driver_headers)
    response.raise_for_status()
    print("List Requested Rides:", response.status_code)
    print_response(response)
except requests.exceptions.RequestException as e:
    print("List Requested Rides Error:", response.status_code if 'response' in locals() else 'N/A')
    if 'response' in locals():
        print_response(response)
    print(f"Exception: {str(e)}")

# %%
# Accept Ride (if any ride_id available)
if 'ride_id' in locals():
    accept_endpoint = f"{BASE_URL}/rides/{ride_id}/accept/"

    try:
        response = requests.post(accept_endpoint, headers=driver_headers)
        response.raise_for_status()
        print("Accept Ride:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Accept Ride Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No ride_id available. Please request a ride first.")

# %%
if 'driver_id' in locals():
    update_ride_endpoint = f"{BASE_URL}/rides/{ride_id}/status/"
    payload = {"status": "in_progress"}
    try:
        response = requests.put(update_ride_endpoint, json=payload, headers=driver_headers)
        response.raise_for_status()
        print("Update Ride Status:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Update Ride Status Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No driver token available. Please login as driver first.")

# %%
"""
## 2.3 Driver Earnings Flow

Luồng xử lý thu nhập của tài xế:
1. Xem tổng quan thu nhập
2. Xem lịch sử thu nhập
3. Rút tiền
"""

# %%
# Driver Earnings Flow
if 'driver_headers' in locals():
    # 1. Get earnings overview
    earnings_endpoint = f"{BASE_URL}/drivers/earnings/overview/"
    try:
        response = requests.get(earnings_endpoint, headers=driver_headers)
        response.raise_for_status()
        print("Earnings Overview:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Earnings Overview Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

    # 2. Get earnings history
    history_endpoint = f"{BASE_URL}/drivers/earnings/history/"
    try:
        response = requests.get(history_endpoint, headers=driver_headers)
        response.raise_for_status()
        print("Earnings History:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Earnings History Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")

    # 3. Withdraw earnings
    withdraw_endpoint = f"{BASE_URL}/drivers/earnings/withdraw/"
    payload = {
        "amount": 1000000,
        "bank_info": {
            "bank_name": "VCB",
            "account_number": "1234567890"
        }
    }
    try:
        response = requests.post(withdraw_endpoint, json=payload, headers=driver_headers)
        response.raise_for_status()
        print("Withdraw Earnings:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Withdraw Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No driver token available. Please login as driver first.")

# %%
"""

"""

# %%
"""
# 3. Admin Flow
"""

# %%
"""
## 3.1 Admin Authentication Flow

Luồng xử lý cho Admin:
1. Đăng nhập Admin
2. Làm mới token
"""

# %%
# Admin Login
login_endpoint = f"{BASE_URL}/auth/token/"
payload = {
    "email": "admin@gmail.com",
    "password": "admin"
}

try:
    response = requests.post(login_endpoint, json=payload)
    response.raise_for_status()
    print("Admin Login:")
    print_response(response)
    admin_headers = headers.copy()
    admin_headers['Authorization'] = f'Bearer {response.json().get("access")}'
    # Lưu token cho các request sau này
    access_token = response.json().get('access')
    headers['Authorization'] = f'Bearer {access_token}'
except requests.exceptions.RequestException as e:
    print("Admin Login Error:", response.status_code, response.json(), f"Exception: {str(e)}")

# %%
"""
## 3.2 Admin System Management Flow

Luồng quản lý hệ thống của Admin:
1. Xem thống kê tổng quan
2. Quản lý tài xế
3. Quản lý khiếu nại
4. Quản lý thanh toán
"""

# %%
#Get list of all drivers profiles that are pending verification
pending_drivers_endpoint = f"{BASE_URL}/drivers/pending/"
try:
    response = requests.get(pending_drivers_endpoint, headers=admin_headers)
    response.raise_for_status()
    print("Pending Driver Profiles:", response.status_code)
    print_response(response)
except requests.exceptions.RequestException as e:
    print("Pending Driver Profiles Error:", response.status_code if 'response' in locals() else 'N/A')
    if 'response' in locals():
        print_response(response)
    print(f"Exception: {str(e)}")

# %%
locals()["driver_id"]

# %%
# Verify a Driver (if driver_id available)
if 'driver_id' in locals():
    verify_endpoint = f"{BASE_URL}/drivers/{driver_id}/verify/"
    payload = {"status": "approved"}

    try:
        response = requests.post(verify_endpoint, json=payload, headers=admin_headers)
        response.raise_for_status()
        print("Verify Driver:", response.status_code, response.json())
    except requests.exceptions.RequestException as e:
        print("Verify Driver Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
else:
    print("No driver_id available. Please register a driver first.")


# %%
# Get Admin Dashboard Stats
dashboard_endpoint = f"{BASE_URL}/admin/dashboard/"

try:
    response = requests.get(dashboard_endpoint, headers=admin_headers)
    response.raise_for_status()
    print("Admin Dashboard:", response.status_code, response.json())
except requests.exceptions.RequestException as e:
    print("Admin Dashboard Error:", response.status_code if 'response' in locals() else 'N/A', f"Exception: {str(e)}")
