let map;
let userMarker;
let userAccuracyCircle;
let watchId;
let directionsService;
let directionsRenderer;
let userLocationPulse;
let startRotateX;
let currentHeading = 0;
let isRotating = false;

function initMap() {
    console.log("Initializing map...");
    const mapElement = document.getElementById("map");
    if (!mapElement) {
        console.error("Map element not found!");
        return;
    }
    
    try {
        map = new google.maps.Map(mapElement, {
            center: { lat: 16.0544, lng: 108.2022 },
            zoom: 15,
            mapTypeControl: false,
            fullscreenControl: false,
            streetViewControl: false,
            rotateControl: true,
            zoomControl: true,
            styles: [{ "featureType": "poi", "stylers": [{ "visibility": "off" }] }]
        });
        console.log("Map initialized!");
        
        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            map: map,
            suppressMarkers: true
        });
        
        initMapControls();
        setupRotationEvents();
        mapElement.style.cursor = 'grab';
        
        setTimeout(getCurrentLocation, 1000);
    } catch (error) {
        console.error("Error initializing map:", error);
        showStatusMessage("Lỗi khởi tạo bản đồ. Vui lòng làm mới trang.", "danger");
    }
}

function initMapControls() {
    try {
        const locationButton = document.getElementById('locationBtn');
        if (locationButton) {
            locationButton.addEventListener('click', () => {
                console.log("Location button clicked");
                getCurrentLocation();
            });
        }
        
        const resetOrientationButton = document.getElementById('resetOrientationBtn');
        if (resetOrientationButton) {
            resetOrientationButton.addEventListener('click', resetMapOrientation);
        }
        
        const connectButton = document.querySelector('.connect-btn');
        if (connectButton) {
            connectButton.addEventListener('click', toggleConnection);
        }
    } catch (error) {
        console.error("Error initializing map controls:", error);
    }
}

function setupRotationEvents() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;
    
    mapElement.addEventListener('mousedown', startRotation);
    mapElement.addEventListener('touchstart', handleTouchStart, { passive: false });
    mapElement.addEventListener('mousemove', rotateMap);
    mapElement.addEventListener('touchmove', handleTouchMove, { passive: false });
    mapElement.addEventListener('mouseup', stopRotation);
    mapElement.addEventListener('touchend', stopRotation);
    mapElement.addEventListener('mouseleave', stopRotation);
}

function startRotation(e) {
    if (e.button !== 0) return;
    if (e.ctrlKey || e.altKey) {
        e.preventDefault();
        isRotating = true;
        startRotateX = e.clientX;
        document.getElementById('map').style.cursor = 'grabbing';
    }
}

function handleTouchStart(e) {
    if (e.touches.length === 2) {
        e.preventDefault();
        isRotating = true;
        startRotateX = e.touches[0].clientX;
    }
}

function rotateMap(e) {
    if (!isRotating || startRotateX === undefined || !map) return;
    e.preventDefault();
    const sensitivity = 0.2;
    const deltaX = e.clientX - startRotateX;
    currentHeading = (currentHeading - deltaX * sensitivity) % 360;
    map.setHeading(currentHeading);
    startRotateX = e.clientX;
}

function handleTouchMove(e) {
    if (!isRotating || startRotateX === undefined || !map) return;
    e.preventDefault();
    if (e.touches.length === 2) {
        const sensitivity = 0.2;
        const deltaX = e.touches[0].clientX - startRotateX;
        currentHeading = (currentHeading - deltaX * sensitivity) % 360;
        map.setHeading(currentHeading);
        startRotateX = e.touches[0].clientX;
    }
}

function stopRotation() {
    if (isRotating) {
        isRotating = false;
        startRotateX = undefined;
        const mapElement = document.getElementById('map');
        if (mapElement) mapElement.style.cursor = 'grab';
    }
}

function resetMapOrientation() {
    if (!map) return;
    currentHeading = 0;
    map.setHeading(0);
    showStatusMessage("Đã đặt lại hướng bản đồ về hướng Bắc", "info", 2000);
}

function getCurrentLocation() {
    console.log("Getting current location...");
    if (!navigator.geolocation) {
        showStatusMessage("Trình duyệt không hỗ trợ định vị", "danger");
        console.error("Geolocation not supported");
        return;
    }
    
    showStatusMessage("Đang xác định vị trí...", "info");
    navigator.geolocation.getCurrentPosition(
        handleLocationSuccess,
        handleLocationError,
        { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
}

function handleLocationSuccess(position) {
    try {
        const pos = {
            lat: position.coords.latitude,
            lng: position.coords.longitude
        };
        console.log("Location coordinates:", pos);
        
        if (!map) {
            console.error("Map not initialized!");
            return;
        }
        
        map.setCenter(pos);
        if (userMarker) {
            userMarker.setPosition(pos);
        } else {
            userMarker = new google.maps.Marker({
                position: pos,
                map: map,
                title: "Vị trí của bạn",
                icon: {
                    path: google.maps.SymbolPath.CIRCLE,
                    scale: 10,
                    fillColor: "#0d8075",
                    fillOpacity: 1,
                    strokeColor: "#FFFFFF",
                    strokeWeight: 2
                },
                zIndex: 2
            });
        }
        
        const accuracy = position.coords.accuracy;
        if (userAccuracyCircle) {
            userAccuracyCircle.setCenter(pos);
            userAccuracyCircle.setRadius(accuracy);
        } else {
            userAccuracyCircle = new google.maps.Circle({
                strokeColor: "#0d8075",
                strokeOpacity: 0.2,
                strokeWeight: 1,
                fillColor: "#0d8075",
                fillOpacity: 0.1,
                map: map,
                center: pos,
                radius: accuracy,
                zIndex: 1
            });
        }
        
        createLocationPulse(pos);
        showStatusMessage("Đã xác định vị trí thành công", "success", 3000);
        startLocationTracking();
    } catch (error) {
        console.error("Error handling location success:", error);
        showStatusMessage("Lỗi xử lý vị trí", "danger", 3000);
    }
}

function createLocationPulse(position) {
    try {
        if (userLocationPulse) {
            userLocationPulse.setMap(null);
        }
        
        if (!map) return;
        
        const pulseDiv = document.createElement('div');
        pulseDiv.className = 'location-pulse';
        const mapContainer = document.querySelector('.map-container');
        if (mapContainer) mapContainer.appendChild(pulseDiv);
        
        function updatePulsePosition() {
            if (!map || !map.getProjection()) return;
            try {
                const projection = map.getProjection();
                const point = projection.fromLatLngToPoint(new google.maps.LatLng(position));
                const mapDiv = map.getDiv();
                const mapRect = mapDiv.getBoundingClientRect();
                const scale = Math.pow(2, map.getZoom());
                const worldPoint = new google.maps.Point(point.x * scale, point.y * scale);
                const centerPoint = projection.fromLatLngToPoint(map.getCenter());
                const centerWorldPoint = new google.maps.Point(centerPoint.x * scale, centerPoint.y * scale);
                const pixelOffset = {
                    x: worldPoint.x - centerWorldPoint.x + (mapRect.width / 2),
                    y: worldPoint.y - centerWorldPoint.y + (mapRect.height / 2)
                };
                pulseDiv.style.left = (pixelOffset.x - 12) + 'px';
                pulseDiv.style.top = (pixelOffset.y - 12) + 'px';
            } catch (error) {
                console.error("Error updating pulse position:", error);
            }
        }
        
        setTimeout(updatePulsePosition, 500);
        google.maps.event.addListener(map, 'bounds_changed', updatePulsePosition);
        
        userLocationPulse = {
            setMap: function(map) {
                if (!map && pulseDiv.parentNode) {
                    pulseDiv.parentNode.removeChild(pulseDiv);
                    google.maps.event.clearListeners(map, 'bounds_changed');
                }
            }
        };
    } catch (error) {
        console.error("Error creating location pulse:", error);
    }
}

function handleLocationError(error) {
    console.error("Location error:", error);
    let message = "Lỗi xác định vị trí";
    switch(error.code) {
        case error.PERMISSION_DENIED:
            message = "Quyền truy cập vị trí bị từ chối.";
            break;
        case error.POSITION_UNAVAILABLE:
            message = "Không thể xác định vị trí.";
            break;
        case error.TIMEOUT:
            message = "Quá thời gian chờ xác định vị trí.";
            break;
        case error.UNKNOWN_ERROR:
            message = "Lỗi không xác định.";
            break;
    }
    showStatusMessage(message, "danger", 5000);
}

function startLocationTracking() {
    console.log("Starting location tracking...");
    stopLocationTracking();
    
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const pos = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                if (userMarker) userMarker.setPosition(pos);
                if (userAccuracyCircle) {
                    userAccuracyCircle.setCenter(pos);
                    userAccuracyCircle.setRadius(position.coords.accuracy);
                }
                const connectBtn = document.querySelector('.connect-btn');
                if (connectBtn && connectBtn.getAttribute('data-connected') === 'true') {
                    map.setCenter(pos);
                }
            },
            (error) => {
                console.error("Error watching position:", error);
                if (error.code !== error.TIMEOUT) handleLocationError(error);
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }
}

function stopLocationTracking() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
        console.log("Location tracking stopped");
    }
}

function toggleConnection() {
    console.log("Toggling connection...");
    const connectBtn = document.querySelector('.connect-btn');
    if (!connectBtn) {
        console.error("Connect button not found");
        return;
    }
    
    const isConnected = connectBtn.getAttribute('data-connected') === 'true';
    const newConnectionState = !isConnected;
    
    connectBtn.setAttribute('data-connected', String(newConnectionState));
    connectBtn.textContent = newConnectionState ? 'Tắt kết nối' : 'Bật kết nối';
    
    const statusBar = document.querySelector('.status-bar span');
    if (statusBar) {
        statusBar.className = `text-${newConnectionState ? 'success' : 'danger'}`;
        statusBar.textContent = `Bạn đang ${newConnectionState ? 'online' : 'offline'}.`;
    }
    
    showStatusMessage(`Đã ${newConnectionState ? 'bật' : 'tắt'} kết nối`, newConnectionState ? 'success' : 'info', 2000);
    
    if (newConnectionState && userMarker) {
        map.setCenter(userMarker.getPosition());
    }
    
    return false;
}

function showStatusMessage(message, type = 'info', duration = 0) {
    try {
        console.log("Status message:", message, type);
        let statusMessage = document.getElementById('statusMessage');
        if (!statusMessage) {
            statusMessage = document.createElement('div');
            statusMessage.id = 'statusMessage';
            statusMessage.className = 'status-message';
            const mapContainer = document.querySelector('.map-container') || document.body;
            mapContainer.appendChild(statusMessage);
        }
        
        statusMessage.textContent = message;
        statusMessage.className = `status-message ${type}`;
        statusMessage.style.display = 'block';
        statusMessage.style.opacity = '1';
        
        if (duration > 0) {
            setTimeout(() => {
                statusMessage.style.opacity = '0';
                setTimeout(() => {
                    statusMessage.style.display = 'none';
                }, 300);
            }, duration);
        }
    } catch (error) {
        console.error("Error showing status message:", error);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log("DOM loaded");
    const mapElement = document.getElementById('map');
    if (mapElement && window.google && window.google.maps) {
        console.log("Google Maps API loaded");
        initMap();
    }
});