from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
from .models import Payment
from .serializers import CODPaymentSerializer, BkashSubmitSerializer, PaymentStatusSerializer
from orders.models import Order


class CODPaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CODPaymentSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.context['order']
        payment = Payment.objects.create(
            order=order,
            method='COD',
            status='PENDING',
            amount=order.total_amount,
        )
        return Response({
            'message': 'COD payment recorded. Pay on delivery.',
            'order_number': order.order_number,
            'amount': str(payment.amount),
            'status': payment.status,
        }, status=status.HTTP_201_CREATED)


class BkashSubmitView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = BkashSubmitSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        order = serializer.context['order']
        payment = Payment.objects.create(
            order=order,
            method='BKASH',
            status='PENDING',
            amount=order.total_amount,
            bkash_number=serializer.validated_data['bkash_number'],
            bkash_transaction_id=serializer.validated_data['bkash_transaction_id'],
        )
        return Response({
            'message': 'bKash payment submitted. Awaiting admin verification.',
            'order_number': order.order_number,
            'amount': str(payment.amount),
            'bkash_merchant_number': settings.BKASH_NUMBER,
            'status': payment.status,
        }, status=status.HTTP_201_CREATED)


class PaymentStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
            payment = order.payment
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        except Payment.DoesNotExist:
            return Response({'detail': 'No payment found for this order.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = PaymentStatusSerializer(payment)
        return Response(serializer.data)
