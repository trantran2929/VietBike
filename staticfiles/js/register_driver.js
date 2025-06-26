let map, userMarker, userAccuracyCircle, watchId, directionsService, directionsRenderer;
let currentHeading = 0, isRotating = false, startRotateX;

function initMap() {
    const mapElement = document.getElementById("map");
    if (!mapElement) {
        console.error("Map element not found!");
        return;
    }

    try {
        map = new google.maps.Map(mapElement, {
            center: { lat: 16.0544, lng: 108.2022 }, // Đà Nẵng
            zoom: 15,
            mapTypeControl: false,
            fullscreenControl: false,
            streetViewControl: false,
            rotateControl: true,
            zoomControl: true,
            styles: [{ featureType: "poi", stylers: [{ visibility: "off" }] }],
        });

        directionsService = new google.maps.DirectionsService();
        directionsRenderer = new google.maps.DirectionsRenderer({
            map: map,
            suppressMarkers: true,
        });

        initMapControls();
        setupRotationEvents();
        mapElement.style.cursor = "grab";
        setTimeout(getCurrentLocation, 1000);
    } catch (error) {
        console.error("Error initializing map:", error);
        showStatusMessage("Lỗi khởi tạo bản đồ. Vui lòng làm mới trang.", "danger");
    }
}

function initMapControls() {
    const locationButton = document.getElementById("locationBtn");
    if (locationButton) {
        locationButton.addEventListener("click", getCurrentLocation);
    }

    const resetOrientationButton = document.getElementById("resetOrientationBtn");
    if (resetOrientationButton) {
        resetOrientationButton.addEventListener("click", resetMapOrientation);
    }
}

function setupRotationEvents() {
    const mapElement = document.getElementById("map");
    if (!mapElement) return;

    mapElement.addEventListener("mousedown", startRotation);
    mapElement.addEventListener("touchstart", handleTouchStart, { passive: false });
    mapElement.addEventListener("mousemove", rotateMap);
    mapElement.addEventListener("touchmove", handleTouchMove, { passive: false });
    mapElement.addEventListener("mouseup", stopRotation);
    mapElement.addEventListener("touchend", stopRotation);
    mapElement.addEventListener("mouseleave", stopRotation);
}

function startRotation(e) {
    if (e.button !== 0 || !e.ctrlKey) return;
    e.preventDefault();
    isRotating = true;
    startRotateX = e.clientX;
    document.getElementById("map").style.cursor = "grabbing";
}

function handleTouchStart(e) {
    if (e.touches.length !== 2) return;
    e.preventDefault();
    isRotating = true;
    startRotateX = e.touches[0].clientX;
}

function rotateMap(e) {
    if (!isRotating || startRotateX === undefined) return;
    e.preventDefault();
    const sensitivity = 0.2;
    const deltaX = e.clientX - startRotateX;
    currentHeading = (currentHeading - deltaX * sensitivity) % 360;
    map.setHeading(currentHeading);
    startRotateX = e.clientX;
}

function handleTouchMove(e) {
    if (!isRotating || startRotateX === undefined || e.touches.length !== 2) return;
    e.preventDefault();
    const sensitivity = 0.2;
    const deltaX = e.touches[0].clientX - startRotateX;
    currentHeading = (currentHeading - deltaX * sensitivity) % 360;
    map.setHeading(currentHeading);
    startRotateX = e.touches[0].clientX;
}

function stopRotation() {
    if (!isRotating) return;
    isRotating = false;
    startRotateX = undefined;
    document.getElementById("map").style.cursor = "grab";
}

function resetMapOrientation() {
    if (!map) return;
    currentHeading = 0;
    map.setHeading(0);
    showStatusMessage("Đã đặt lại hướng bản đồ", "info", 2000);
}

function getCurrentLocation() {
    if (!navigator.geolocation) {
        showStatusMessage("Trình duyệt không hỗ trợ định vị", "danger");
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
    const pos = { lat: position.coords.latitude, lng: position.coords.longitude };

    if (!map) return;

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
                strokeWeight: 2,
            },
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
        });
    }

    showStatusMessage("Đã xác định vị trí", "success", 2000);
    startLocationTracking();
}

function handleLocationError(error) {
    let message;
    switch (error.code) {
        case error.PERMISSION_DENIED:
            message = "Quyền truy cập vị trí bị từ chối";
            break;
        case error.POSITION_UNAVAILABLE:
            message = "Không thể xác định vị trí";
            break;
        case error.TIMEOUT:
            message = "Quá thời gian chờ";
            break;
        default:
            message = "Lỗi không xác định";
    }
    showStatusMessage(message, "danger", 5000);
}

function startLocationTracking() {
    stopLocationTracking();
    if (navigator.geolocation) {
        watchId = navigator.geolocation.watchPosition(
            (position) => {
                const pos = { lat: position.coords.latitude, lng: position.coords.longitude };
                if (userMarker) userMarker.setPosition(pos);
                if (userAccuracyCircle) {
                    userAccuracyCircle.setCenter(pos);
                    userAccuracyCircle.setRadius(position.coords.accuracy);
                }
                if (document.querySelector(".connect-btn")?.getAttribute("data-connected") === "true") {
                    map.setCenter(pos);
                }
            },
            handleLocationError,
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
        );
    }
}

function stopLocationTracking() {
    if (watchId) {
        navigator.geolocation.clearWatch(watchId);
        watchId = null;
    }
}

function showStatusMessage(message, type = "info", duration = 0) {
    let statusMessage = document.getElementById("statusMessage");
    if (!statusMessage) {
        statusMessage = document.createElement("div");
        statusMessage.id = "statusMessage";
        statusMessage.className = "fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded shadow-lg text-white";
        document.body.appendChild(statusMessage);
    }

    statusMessage.textContent = message;
    statusMessage.className = `fixed top-4 left-1/2 transform -translate-x-1/2 px-4 py-2 rounded shadow-lg text-white bg-${type === "success" ? "green" : type === "danger" ? "red" : "blue"}-500`;
    statusMessage.style.display = "block";

    if (duration > 0) {
        setTimeout(() => {
            statusMessage.style.opacity = "0";
            setTimeout(() => (statusMessage.style.display = "none"), 300);
        }, duration);
    }
}

function setupDriverForm() {
    const driverForm = document.getElementById("driverForm");
    if (!driverForm) return;

    driverForm.addEventListener("submit", (e) => {
        const requiredFields = driverForm.querySelectorAll("[required]");
        let isValid = true;

        requiredFields.forEach((field) => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add("border-red-500");
                showFieldError(field, "Vui lòng điền thông tin này");
            } else {
                field.classList.remove("border-red-500");
                clearFieldError(field);
            }
        });

        const emailField = driverForm.querySelector('[type="email"]');
        if (emailField && emailField.value.trim() && !validateEmail(emailField.value.trim())) {
            isValid = false;
            emailField.classList.add("border-red-500");
            showFieldError(emailField, "Email không hợp lệ");
        }

        const phoneField = driverForm.querySelector('[name="phone"]');
        if (phoneField && phoneField.value.trim() && !validatePhoneNumber(phoneField.value.trim())) {
            isValid = false;
            phoneField.classList.add("border-red-500");
            showFieldError(phoneField, "Số điện thoại không hợp lệ");
        }

        const idNumberField = driverForm.querySelector('[name="id_number"]');
        if (idNumberField && idNumberField.value.trim() && !validateIdNumber(idNumberField.value.trim())) {
            isValid = false;
            idNumberField.classList.add("border-red-500");
            showFieldError(idNumberField, "Số CMND/CCCD không hợp lệ");
        }

        const fileFields = driverForm.querySelectorAll('input[type="file"]');
        fileFields.forEach((field) => {
            if (!field.files.length) {
                isValid = false;
                field.classList.add("border-red-500");
                showFieldError(field, "Vui lòng chọn file");
            } else if (field.files[0].size > 5 * 1024 * 1024) {
                isValid = false;
                field.classList.add("border-red-500");
                showFieldError(field, "File quá lớn (tối đa 5MB)");
            } else {
                field.classList.remove("border-red-500");
                clearFieldError(field);
            }
        });

        if (!isValid) {
            e.preventDefault();
            showStatusMessage("Vui lòng điền đầy đủ và chính xác thông tin", "danger", 5000);
        }
    });

    driverForm.querySelectorAll("input").forEach((field) => {
        field.addEventListener("input", () => {
            field.classList.remove("border-red-500");
            clearFieldError(field);
        });
    });
}

function showFieldError(field, message) {
    clearFieldError(field);
    const errorDiv = document.createElement("div");
    errorDiv.className = "text-red-500 text-sm mt-1";
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    const existingError = field.parentNode.querySelector(".text-red-500");
    if (existingError) existingError.remove();
}

function validateEmail(email) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function validatePhoneNumber(phone) {
    return /^(0|\+84)\d{9,10}$/.test(phone);
}

function validateIdNumber(id) {
    return /^\d{9}(\d{3})?$/.test(id);
}

document.addEventListener("DOMContentLoaded", () => {
    setupDriverForm();
    if (document.getElementById("map") && window.google && window.google.maps) {
        initMap();
    }
});
