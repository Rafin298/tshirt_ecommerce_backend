from django.contrib import admin
from django.utils.html import format_html
from .models import Cart, CartItem, Coupon, Order, OrderItem


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ['code', 'discount_type', 'discount_value', 'min_order_value', 'uses_count', 'max_uses', 'is_active', 'expires_at']
    list_filter = ['discount_type', 'is_active']
    search_fields = ['code']
    list_editable = ['is_active']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product_name', 'variant_sku', 'variant_attributes', 'unit_price', 'quantity', 'total_price']
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'total_amount', 'payment_method', 'payment_status', 'status', 'created_at']
    list_filter = ['status', 'payment_method', 'payment_status', 'created_at']
    search_fields = ['order_number', 'user__email', 'user__phone']
    readonly_fields = ['order_number', 'user', 'subtotal', 'discount_amount', 'total_amount', 'coupon_code', 'created_at']
    inlines = [OrderItemInline]
    fields = [
        'order_number', 'user', 'status', 'payment_method', 'payment_status',
        'subtotal', 'discount_amount', 'total_amount', 'coupon_code',
        'shipping_name', 'shipping_phone', 'shipping_division', 'shipping_district',
        'shipping_thana', 'shipping_postal_code', 'shipping_full_address',
        'tracking_note', 'created_at',
    ]
    actions = ['mark_confirmed', 'mark_shipped', 'mark_delivered']

    def mark_confirmed(self, request, queryset):
        queryset.filter(status='PENDING').update(status='CONFIRMED')
    mark_confirmed.short_description = 'Mark selected orders as CONFIRMED'

    def mark_shipped(self, request, queryset):
        queryset.filter(status__in=['CONFIRMED', 'PROCESSING']).update(status='SHIPPED')
    mark_shipped.short_description = 'Mark selected orders as SHIPPED'

    def mark_delivered(self, request, queryset):
        queryset.filter(status='SHIPPED').update(status='DELIVERED')
    mark_delivered.short_description = 'Mark selected orders as DELIVERED'
