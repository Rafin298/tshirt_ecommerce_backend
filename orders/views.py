from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.db import transaction
from django.utils import timezone
from .models import Cart, CartItem, Order, OrderItem, Coupon
from .serializers import (
    CartSerializer, AddCartItemSerializer, UpdateCartItemSerializer,
    ApplyCouponSerializer, PlaceOrderSerializer, OrderSerializer, OrderListSerializer,
)
from products.models import Variant, StockMovement


def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user=user)
    return cart


class CartView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = get_or_create_cart(request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)


class CartAddView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = get_or_create_cart(request.user)
        variant = serializer.validated_data['variant']
        quantity = serializer.validated_data['quantity']

        cart_item, created = CartItem.objects.get_or_create(cart=cart, variant=variant)
        if not created:
            new_qty = cart_item.quantity + quantity
            if new_qty > variant.stock_quantity:
                return Response({'detail': f'Only {variant.stock_quantity} units available.'}, status=status.HTTP_400_BAD_REQUEST)
            cart_item.quantity = new_qty
        else:
            cart_item.quantity = quantity
        cart_item.save()

        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class CartItemUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        cart = get_or_create_cart(request.user)
        try:
            cart_item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UpdateCartItemSerializer(data=request.data, context={'cart_item': cart_item})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart_item.quantity = serializer.validated_data['quantity']
        cart_item.save()
        return Response(CartSerializer(cart).data)

    def delete(self, request, pk):
        cart = get_or_create_cart(request.user)
        try:
            cart_item = CartItem.objects.get(pk=pk, cart=cart)
        except CartItem.DoesNotExist:
            return Response({'detail': 'Cart item not found.'}, status=status.HTTP_404_NOT_FOUND)
        cart_item.delete()
        return Response(CartSerializer(cart).data)


class CartClearView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.items.all().delete()
        cart.coupon = None
        cart.save()
        return Response({'message': 'Cart cleared.'})


class ApplyCouponView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        cart = get_or_create_cart(request.user)
        serializer = ApplyCouponSerializer(data=request.data, context={'cart': cart})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        coupon = serializer.context['coupon']
        cart.coupon = coupon
        cart.save()
        return Response(CartSerializer(cart).data)

    def delete(self, request):
        cart = get_or_create_cart(request.user)
        cart.coupon = None
        cart.save()
        return Response(CartSerializer(cart).data)


class PlaceOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PlaceOrderSerializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        cart = get_or_create_cart(request.user)
        if not cart.items.exists():
            return Response({'detail': 'Your cart is empty.'}, status=status.HTTP_400_BAD_REQUEST)

        address = serializer.context['address']
        payment_method = serializer.validated_data['payment_method']

        try:
            with transaction.atomic():
                # Lock variants for update to prevent race conditions
                variant_ids = list(cart.items.values_list('variant_id', flat=True))
                variants = Variant.objects.select_for_update().filter(id__in=variant_ids)
                variant_map = {v.id: v for v in variants}

                # Validate stock for all items
                cart_items = list(cart.items.select_related('variant'))
                for item in cart_items:
                    variant = variant_map[item.variant_id]
                    if variant.stock_quantity < item.quantity:
                        return Response(
                            {'detail': f'Sorry, "{variant.product.name} ({variant.sku})" is out of stock.'},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                subtotal = cart.get_subtotal()
                discount_amount = cart.get_discount()
                total_amount = subtotal - discount_amount

                # Create order
                order = Order.objects.create(
                    user=request.user,
                    payment_method=payment_method,
                    subtotal=subtotal,
                    discount_amount=discount_amount,
                    total_amount=total_amount,
                    coupon_code=cart.coupon.code if cart.coupon else None,
                    shipping_name=address.recipient_name,
                    shipping_phone=address.phone,
                    shipping_division=address.division,
                    shipping_district=address.district,
                    shipping_thana=address.thana,
                    shipping_postal_code=address.postal_code,
                    shipping_full_address=address.full_address,
                )

                # Create order items and decrement stock
                for item in cart_items:
                    variant = variant_map[item.variant_id]
                    from products.models import VariantAttribute
                    va_qs = VariantAttribute.objects.filter(variant=variant).select_related('attribute_value__attribute')
                    attrs_snapshot = {va.attribute_value.attribute.name: va.attribute_value.value for va in va_qs}

                    OrderItem.objects.create(
                        order=order,
                        variant=variant,
                        product_name=variant.product.name,
                        variant_sku=variant.sku,
                        variant_attributes=attrs_snapshot,
                        unit_price=variant.price,
                        quantity=item.quantity,
                        total_price=variant.price * item.quantity,
                    )

                    variant.stock_quantity -= item.quantity
                    variant.save()
                    StockMovement.objects.create(
                        variant=variant,
                        change=-item.quantity,
                        reason='SALE',
                        note=f'Order {order.order_number}',
                    )

                # Increment coupon uses
                if cart.coupon:
                    Coupon.objects.filter(pk=cart.coupon.pk).update(uses_count=cart.coupon.uses_count + 1)

                # Clear cart
                cart.items.all().delete()
                cart.coupon = None
                cart.save()

        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = Order.objects.filter(user=request.user)

        # Filter
        order_status = request.GET.get('status')
        if order_status:
            orders = orders.filter(status=order_status)
        payment_method = request.GET.get('payment_method')
        if payment_method:
            orders = orders.filter(payment_method=payment_method)

        paginator = PageNumberPagination()
        paginator.page_size = int(request.GET.get('page_size', 20))
        page = paginator.paginate_queryset(orders, request)
        serializer = OrderListSerializer(page, many=True)
        return paginator.get_paginated_response(serializer.data)


class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, order_number):
        try:
            order = Order.objects.prefetch_related('items').get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


class CancelOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, order_number):
        try:
            order = Order.objects.get(order_number=order_number, user=request.user)
        except Order.DoesNotExist:
            return Response({'detail': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)

        if order.status not in ('PENDING', 'CONFIRMED'):
            return Response(
                {'detail': 'Only PENDING or CONFIRMED orders can be cancelled.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in order.items.select_related('variant'):
                if item.variant:
                    variant = Variant.objects.select_for_update().get(pk=item.variant.pk)
                    variant.stock_quantity += item.quantity
                    variant.save()
                    StockMovement.objects.create(
                        variant=variant,
                        change=item.quantity,
                        reason='CANCELLATION',
                        note=f'Cancelled order {order.order_number}',
                    )

            order.status = 'CANCELLED'
            order.save()

        return Response({'message': 'Order cancelled successfully.', 'order_number': order.order_number})
