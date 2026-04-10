from rest_framework import serializers
from .models import Payment
from orders.models import Order


class CODPaymentSerializer(serializers.Serializer):
    order_number = serializers.CharField()

    def validate_order_number(self, value):
        user = self.context['request'].user
        try:
            order = Order.objects.get(order_number=value, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError('Order not found.')
        if order.payment_method != 'COD':
            raise serializers.ValidationError('This order is not a COD order.')
        if hasattr(order, 'payment'):
            raise serializers.ValidationError('Payment already recorded for this order.')
        self.context['order'] = order
        return value


class BkashSubmitSerializer(serializers.Serializer):
    order_number = serializers.CharField()
    bkash_number = serializers.RegexField(
        regex=r'^01[3-9]\d{8}$',
        error_messages={'invalid': 'Enter a valid Bangladeshi bKash number.'},
    )
    bkash_transaction_id = serializers.CharField(max_length=100)

    def validate_order_number(self, value):
        user = self.context['request'].user
        try:
            order = Order.objects.get(order_number=value, user=user)
        except Order.DoesNotExist:
            raise serializers.ValidationError('Order not found.')
        if order.payment_method != 'BKASH':
            raise serializers.ValidationError('This order is not a bKash order.')
        if hasattr(order, 'payment'):
            raise serializers.ValidationError('Payment already submitted for this order.')
        self.context['order'] = order
        return value


class PaymentStatusSerializer(serializers.ModelSerializer):
    order_number = serializers.CharField(source='order.order_number')

    class Meta:
        model = Payment
        fields = ['order_number', 'method', 'status', 'amount', 'bkash_number', 'bkash_transaction_id', 'created_at']
