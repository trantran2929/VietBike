document.addEventListener('DOMContentLoaded', function () {
    // Khởi tạo carousel
    var carousel = new bootstrap.Carousel(document.getElementById('carouselExample'), {
        interval: 5000
    });

    // Kiểm tra trạng thái đăng nhập và điều hướng
    const bookRideButton = document.querySelector('.hero-cta .btn-hero');
    if (bookRideButton) {
        bookRideButton.addEventListener('click', function (event) {
            const accessToken = localStorage.getItem('access_token') || null;

            if (!accessToken) {
                event.preventDefault(); // Ngăn chặn điều hướng mặc định
                const errorMessage = document.getElementById('error-message') || document.createElement('div');
                errorMessage.textContent = 'Vui lòng đăng nhập để đặt chuyến đi.';
                errorMessage.id = 'error-message';
                errorMessage.className = 'text-danger mt-2';
                errorMessage.style.display = 'block';
                this.parentElement.appendChild(errorMessage);

                setTimeout(() => {
                    window.location.href = '/auth/login/'; // Điều hướng đến trang đăng nhập
                }, 2000);
            } else {
                // Điều hướng đến trang đặt chuyến nếu đã đăng nhập
                window.location.href = '/customer/book/'; // URL từ frontend:customer:book_ride
            }
        });
    }

    // Xử lý thêm cho nút "Đặt Chuyến Ngay" trong intro-actions (nếu có)
    const introBookRideButton = document.querySelector('.intro-actions .btn-primary');
    if (introBookRideButton) {
        introBookRideButton.addEventListener('click', function (event) {
            const accessToken = localStorage.getItem('access_token') || null;

            if (!accessToken) {
                event.preventDefault();
                const errorMessage = document.getElementById('error-message') || document.createElement('div');
                errorMessage.textContent = 'Vui lòng đăng nhập để đặt chuyến đi.';
                errorMessage.id = 'error-message';
                errorMessage.className = 'text-danger mt-2';
                errorMessage.style.display = 'block';
                this.parentElement.appendChild(errorMessage);

                setTimeout(() => {
                    window.location.href = '/auth/login/';
                }, 2000);
            } else {
                window.location.href = '/customer/book/';
            }
        });
    }
});

document.addEventListener('DOMContentLoaded', function () {
    var carousel = new bootstrap.Carousel(document.getElementById('carouselExample'), {
        interval: 5000
    });

    const bookRideButton = document.querySelector('.hero-cta .btn-hero');
    if (bookRideButton) {
        bookRideButton.addEventListener('click', function (event) {
            const accessToken = localStorage.getItem('access_token') || null;
            if (!accessToken) {
                event.preventDefault();
                const errorMessage = document.getElementById('error-message') || document.createElement('div');
                errorMessage.textContent = 'Vui lòng đăng nhập để đặt chuyến đi.';
                errorMessage.id = 'error-message';
                errorMessage.className = 'text-danger mt-2';
                errorMessage.style.display = 'block';
                this.parentElement.appendChild(errorMessage);
                setTimeout(() => {
                    window.location.href = '/auth/login/';
                }, 2000);
            } else {
                window.location.href = '/customer/book/'; // Không truyền ride.id
            }
        });
    }

    const introBookRideButton = document.querySelector('.intro-actions .btn-primary');
    if (introBookRideButton) {
        introBookRideButton.addEventListener('click', function (event) {
            const accessToken = localStorage.getItem('access_token') || null;
            if (!accessToken) {
                event.preventDefault();
                const errorMessage = document.getElementById('error-message') || document.createElement('div');
                errorMessage.textContent = 'Vui lòng đăng nhập để đặt chuyến đi.';
                errorMessage.id = 'error-message';
                errorMessage.className = 'text-danger mt-2';
                errorMessage.style.display = 'block';
                this.parentElement.appendChild(errorMessage);
                setTimeout(() => {
                    window.location.href = '/auth/login/';
                }, 2000);
            } else {
                window.location.href = '/customer/book/'; // Không truyền ride.id
            }
        });
    }
});