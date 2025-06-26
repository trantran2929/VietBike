#!/usr/bin/env python
import os
import sys

def main():
    """
    Script để xóa sạch database (flush) và chạy migrate lại.
    Chỉ nên dùng trong môi trường phát triển, tránh chạy trên môi trường production.
    """
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'VietBike.settings')
    try:
        import django
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Không thể import Django. Hãy cài đặt Django hoặc chỉnh PYTHONPATH."
        ) from exc
    
    # Khởi tạo Django
    django.setup()

    # 1) Xóa sạch dữ liệu trong DB
    #    (flush sẽ xóa toàn bộ dữ liệu, giữ nguyên cấu trúc)
    execute_from_command_line(['manage.py', 'flush', '--no-input'])

    # 2) Chạy migrate lại (tạo bảng, thêm cột, v.v.)
    execute_from_command_line(['manage.py', 'migrate'])

if __name__ == '__main__':
    # Gọi hàm main
    main()
