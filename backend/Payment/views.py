#backend/Payment/views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from backend.models import Ride, Payment, Notification
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class PaymentView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        user = request.user
        if user.role != 'customer':
            return Response({'error': 'Chỉ khách hàng mới có thể thanh toán.'}, status=status.HTTP_403_FORBIDDEN)
        ride_id = request.data.get('ride_id')
        method = request.data.get('method')
        transaction_id = request.data.get('transaction_id')
        if not all([ride_id, method]):
            return Response({'error': 'Vui lòng cung cấp ID chuyến đi và phương thức thanh toán.'}, status=status.HTTP_400_BAD_REQUEST)
        if method not in ['cash', 'momo', 'card']:
            return Response({'error': 'Phương thức thanh toán không hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)
        if method in ['momo', 'card'] and not transaction_id:
            return Response({'error': 'Vui lòng cung cấp ID giao dịch cho Momo hoặc thẻ.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            ride = Ride.objects.select_related('user', 'driver').get(id=ride_id, user=user, status='completed')
            if Payment.objects.filter(ride=ride).exists():
                return Response({'error': 'Chuyến đi đã được thanh toán.'}, status=status.HTTP_400_BAD_REQUEST)
            payment = Payment.objects.create(
                ride=ride, amount=ride.fare, method=method,
                status='completed' if method == 'cash' else 'pending',
                transaction_id=transaction_id if method in ['momo', 'card'] else None
            )
            Notification.objects.create(
                user=user, ride=ride,
                message=f"Thanh toán {method} cho chuyến đi {ride.id} đã được ghi nhận."
            )
            if ride.driver and method in ['momo', 'card']:
                Notification.objects.create(
                    user=ride.driver.user, ride=ride,
                    message=f"Khách hàng {user.username} đã thanh toán {method} cho chuyến đi {ride.id}."
                )
            return Response({
                'message': 'Thanh toán thành công!',
                'payment': {
                    'ride_id': ride.id,
                    'amount': float(payment.amount),
                    'method': payment.method,
                    'status': payment.status,
                    'created_at': payment.created_at
                }
            }, status=status.HTTP_201_CREATED)
        except Ride.DoesNotExist:
            return Response({'error': 'Chuyến đi không tồn tại hoặc không thuộc về bạn.'}, status=status.HTTP_404_NOT_FOUND)