document.addEventListener('DOMContentLoaded', function () {
    // Khởi tạo Mapbox
    mapboxgl.accessToken = 'YOUR_MAPBOX_ACCESS_TOKEN'; // Thay bằng token Mapbox của bạn
    const map = new mapboxgl.Map({
        container: 'map',
        style: 'mapbox://styles/mapbox/streets-v11',
        center: [106.6297, 10.8231], // Tọa độ mặc định (TP.HCM)
        zoom: 12
    });

    // Thêm marker mock cho điểm đi/đến
    const pickupMarker = new mapboxgl.Marker({ color: '#FF5733' })
        .setLngLat([{{ ride.start_location.longitude|default:106.6297 }}, {{ ride.start_location.latitude|default:10.8231 }}])
        .addTo(map);
    const destinationMarker = new mapboxgl.Marker({ color: '#33FF57' })
        .setLngLat([{{ ride.end_location.longitude|default:106.6797 }}, {{ ride.end_location.latitude|default:10.7731 }}])
        .addTo(map);

    // Thêm marker mock cho tài xế
    let driverMarker = null;

    // Theo dõi vị trí tài xế
    if (rideId) {
        const trackInterval = setInterval(() => {
            const accessToken = localStorage.getItem('access_token');
            fetch(`/api/rides/${rideId}/track/`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                }
            })
            .then(response => response.json())
            .then(data => {
                if (data.driver_location) {
                    const [lng, lat] = data.driver_location;
                    if (!driverMarker) {
                        driverMarker = new mapboxgl.Marker({ color: '#00F' })
                            .setLngLat([lng, lat])
                            .addTo(map);
                    } else {
                        driverMarker.setLngLat([lng, lat]);
                    }
                    map.flyTo({ center: [lng, lat], zoom: 14 });

                    document.getElementById('acceptedState').style.display = 'block';
                    document.getElementById('waitingState').style.display = 'none';
                    document.getElementById('pickupLocationAccepted').textContent = `(${pickupMarker.getLngLat().lat.toFixed(4)}, ${pickupMarker.getLngLat().lng.toFixed(4)})`;
                    document.getElementById('dropoffLocationAccepted').textContent = `(${destinationMarker.getLngLat().lat.toFixed(4)}, ${destinationMarker.getLngLat().lng.toFixed(4)})`;
                    document.getElementById('fareAccepted').textContent = `${data.fare}đ`;
                    document.getElementById('driverName').textContent = data.driver_name || 'Chưa có';
                    document.getElementById('vehicleType').textContent = '{{ ride.vehicle_type|default:"Xe máy" }}';
                    document.getElementById('arrivalTime').textContent = data.estimated_arrival || 'Chưa có';
                }
            })
            .catch(error => {
                console.error('Tracking error:', error);
                alert('Không thể theo dõi chuyến đi. Vui lòng thử lại sau.');
            });
        }, 5000);

        document.getElementById('cancelWaitingRide').addEventListener('click', () => {
            clearInterval(trackInterval);
            window.location.href = '/customer/book/';
        });
    }
});