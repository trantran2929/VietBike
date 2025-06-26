document.addEventListener('DOMContentLoaded', function () {
    // Khởi tạo Mapbox
    mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN'; // Thay bằng token Mapbox của bạn
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [106.6297, 10.8231], // Tọa độ mặc định (TP.HCM)
        zoom: 12
    });

    // Biến lưu tọa độ
    let pickupCoords = null;
    let destinationCoords = null;

    // Thêm marker mock cho điểm đi/đến
    const pickupMarker = new mapboxgl.Marker({ color: '#FF5733' })
        .setLngLat([106.6297, 10.8231])
        .addTo(map);
    const destinationMarker = new mapboxgl.Marker({ color: '#33FF57' })
        .setLngLat([106.6797, 10.7731])
        .addTo(map);

    // Thêm marker mock cho tài xế
    let driverMarker = null;

    // Cập nhật tọa độ khi click trên bản đồ
    map.on('click', (e) => {
        if (!pickupCoords) {
            pickupCoords = [e.lngLat.lng, e.lngLat.lat];
            pickupMarker.setLngLat(pickupCoords);
            document.getElementById('pickup_location').value = `(${pickupCoords[1].toFixed(4)}, ${pickupCoords[0].toFixed(4)})`;
        } else if (!destinationCoords) {
            destinationCoords = [e.lngLat.lng, e.lngLat.lat];
            destinationMarker.setLngLat(destinationCoords);
            document.getElementById('destination_location').value = `(${destinationCoords[1].toFixed(4)}, ${destinationCoords[0].toFixed(4)})`;
        }
        updateEstimatedFare();
    });

    // Nút đặt tọa độ thủ công
    document.getElementById('setPickup').addEventListener('click', () => {
        const input = prompt('Nhập tọa độ điểm đón (lat, lng): ví dụ 10.8231, 106.6297');
        if (input) {
            const [lat, lng] = input.split(',').map(Number);
            if (lat && lng) {
                pickupCoords = [lng, lat];
                pickupMarker.setLngLat(pickupCoords);
                document.getElementById('pickup_location').value = `(${lat.toFixed(4)}, ${lng.toFixed(4)})`;
                updateEstimatedFare();
            }
        }
    });

    document.getElementById('setDestination').addEventListener('click', () => {
        const input = prompt('Nhập tọa độ điểm đến (lat, lng): ví dụ 10.7731, 106.6797');
        if (input) {
            const [lat, lng] = input.split(',').map(Number);
            if (lat && lng) {
                destinationCoords = [lng, lat];
                destinationMarker.setLngLat(destinationCoords);
                document.getElementById('destination_location').value = `(${lat.toFixed(4)}, ${lng.toFixed(4)})`;
                updateEstimatedFare();
            }
        }
    });

    // Cập nhật giá ước tính
    function updateEstimatedFare() {
        if (pickupCoords && destinationCoords) {
            const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
            const accessToken = localStorage.getItem('access_token') || null;
            const vehicleType = document.getElementById('vehicle_type').value;

            if (accessToken) {
                fetch('/api/rides/request/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${accessToken}`,
                        'X-CSRFToken': csrfToken
                    },
                    body: JSON.stringify({
                        start_location: pickupCoords,
                        end_location: destinationCoords,
                        vehicle_type: vehicleType
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.fare) {
                        document.getElementById('estimated_fare').textContent = `${data.fare}đ`;
                    } else {
                        document.getElementById('estimated_fare').textContent = 'Không tính được';
                    }
                })
                .catch(error => console.error('Error fetching fare:', error));
            }
        }
    }

    // Xử lý xác nhận đặt chuyến
    document.getElementById('confirmBooking').addEventListener('click', function () {
        if (!pickupCoords || !destinationCoords) {
            alert('Vui lòng chọn điểm đi và điểm đến!');
            return;
        }

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        const accessToken = localStorage.getItem('access_token') || null;
        const vehicleType = document.getElementById('vehicle_type').value;

        if (!accessToken) {
            alert('Vui lòng đăng nhập để đặt chuyến!');
            window.location.href = '/auth/login/';
            return;
        }

        this.disabled = true;
        this.textContent = 'Đang xử lý...';

        fetch('/api/rides/request/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${accessToken}`,
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                start_location: pickupCoords,
                end_location: destinationCoords,
                vehicle_type: vehicleType
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.ride && data.ride.id) {
                // Điều hướng đến trang theo dõi với ride_id
                window.location.href = `/customer/ride/${data.ride.id}/track/`;
            } else {
                alert(data.error || 'Có lỗi khi đặt chuyến!');
            }
        })
        .catch(error => console.error('Error:', error))
        .finally(() => {
            this.disabled = false;
            this.textContent = 'Xác nhận đặt chuyến';
        });
    });

    document.getElementById('vehicle_type').addEventListener('change', updateEstimatedFare);
});