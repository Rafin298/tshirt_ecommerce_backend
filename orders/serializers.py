from rest_framework import serializers
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, Coupon
from products.models import Variant
from users.models import Address
from products.serializers import VariantSerializer


class CartItemSerializer(serializers.ModelSerializer):
    variant_sku = serializers.CharField(source='variant.sku', read_only=True)
    product_name = serializers.CharField(source='variant.product.name', read_only=True)
    unit_price = serializers.DecimalField(source='variant.price', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(source='variant.is_in_stock', read_only=True)
    stock_quantity = serializers.IntegerField(source='variant.stock_quantity', read_only=True)
    attributes = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = [
            'id', 'variant', 'variant_sku', 'product_name',
            'unit_price', 'quantity', 'total_price',
            'is_in_stock', 'stock_quantity', 'attributes',
        ]

    def get_total_price(self, obj):
        return obj.variant.price * obj.quantity

    def get_attributes(self, obj):
        from products.models import VariantAttribute
        va_qs = VariantAttribute.objects.filter(variant=obj.variant).select_related('attribute_value__attribute')
        return {va.attribute_value.attribute.name: va.attribute_value.value for va in va_qs}


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    subtotal = serializers.SerializerMethodField()
    discount = serializers.SerializerMethodField()
    total = serializers.SerializerMethodField()
    coupon_code = serializers.SerializerMethodField()

    class Meta:
        model = Cart
        fields = ['id', 'items', 'coupon_code', 'subtotal', 'discount', 'total']

    def get_subtotal(self, obj):
        return obj.get_subtotal()

    def get_discount(self, obj):
        return obj.get_discount()

    def get_total(self, obj):
        return obj.get_total()

    def get_coupon_code(self, obj):
        return obj.coupon.code if obj.coupon else None


class AddCartItemSerializer(serializers.Serializer):
    variant_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        try:
            variant = Variant.objects.get(pk=data['variant_id'], is_active=True)
        except Variant.DoesNotExist:
            raise serializers.ValidationError({'variant_id': 'Variant not found or inactive.'})
        if variant.stock_quantity == 0:
            raise serializers.ValidationError({'variant_id': 'This item is out of stock.'})
        if data['quantity'] > variant.stock_quantity:
            raise serializers.ValidationError({'quantity': f'Only {variant.stock_quantity} units available.'})
        data['variant'] = variant
        return data


class UpdateCartItemSerializer(serializers.Serializer):
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, data):
        cart_item = self.context.get('cart_item')
        if data['quantity'] > cart_item.variant.stock_quantity:
            raise serializers.ValidationError({'quantity': f'Only {cart_item.variant.stock_quantity} units available.'})
        return data


class ApplyCouponSerializer(serializers.Serializer):
    code = serializers.CharField()

    def validate_code(self, value):
        value = value.upper()
        try:
            coupon = Coupon.objects.get(code=value, is_active=True)
        except Coupon.DoesNotExist:
            raise serializers.ValidationError('Invalid or inactive coupon code.')
        if coupon.expires_at and coupon.expires_at < timezone.now():
            raise serializers.ValidationError('This coupon has expired.')
        if coupon.max_uses is not None and coupon.uses_count >= coupon.max_uses:
            raise serializers.ValidationError('This coupon has reached its usage limit.')
        self.context['coupon'] = coupon
        return value

    def validate(self, data):
        cart = self.context.get('cart')
        coupon = self.context.get('coupon')
        subtotal = cart.get_subtotal()
        if subtotal < coupon.min_order_value:
            raise serializers.ValidationError(
                f'Minimum order value for this coupon is BDT {coupon.min_order_value}.'
            )
        return data


class PlaceOrderSerializer(serializers.Serializer):
    address_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=['COD', 'BKASH'])

    def validate_address_id(self, value):
        user = self.context['request'].user
        try:
            address = Address.objects.get(pk=value, user=user)
        except Address.DoesNotExist:
            raise serializers.ValidationError('Address not found.')
        self.context['address'] = address
        return value


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['product_name', 'variant_sku', 'variant_attributes', 'unit_price', 'quantity', 'total_price']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    shipping_address = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = [
            'order_number', 'status', 'payment_method', 'payment_status',
            'subtotal', 'discount_amount', 'total_amount',
            'coupon_code', 'tracking_note', 'shipping_address',
            'items', 'created_at',
        ]

    def get_shipping_address(self, obj):
        return {
            'recipient_name': obj.shipping_name,
            'phone': obj.shipping_phone,
            'division': obj.shipping_division,
            'district': obj.shipping_district,
            'thana': obj.shipping_thana,
            'postal_code': obj.shipping_postal_code,
            'full_address': obj.shipping_full_address,
        }


class OrderListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['order_number', 'status', 'payment_method', 'payment_status', 'total_amount', 'created_at']
