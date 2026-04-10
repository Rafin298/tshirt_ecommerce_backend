import random
import string
from datetime import date
from django.db import models
from django.contrib.auth import get_user_model
from users.models import Address
from products.models import Variant

User = get_user_model()


def generate_order_number():
    date_str = date.today().strftime('%Y%m%d')
    random_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    return f"ORD-{date_str}-{random_str}"


DISCOUNT_TYPE_CHOICES = [
    ('FLAT', 'Flat'),
    ('PERCENTAGE', 'Percentage'),
]

ORDER_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('CONFIRMED', 'Confirmed'),
    ('PROCESSING', 'Processing'),
    ('SHIPPED', 'Shipped'),
    ('DELIVERED', 'Delivered'),
    ('CANCELLED', 'Cancelled'),
    ('REFUNDED', 'Refunded'),
]

PAYMENT_METHOD_CHOICES = [
    ('COD', 'Cash on Delivery'),
    ('BKASH', 'bKash'),
]

PAYMENT_STATUS_CHOICES = [
    ('PENDING', 'Pending'),
    ('VERIFIED', 'Verified'),
    ('COLLECTED', 'Collected'),
    ('FAILED', 'Failed'),
]


class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=10, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2)
    min_order_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text='Leave blank for unlimited')
    uses_count = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text='Leave blank to never expire')
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        self.code = self.code.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.code


class Cart(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='cart')
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.email}"

    def get_subtotal(self):
        return sum(item.variant.price * item.quantity for item in self.items.select_related('variant'))

    def get_discount(self):
        if not self.coupon:
            return 0
        subtotal = self.get_subtotal()
        if self.coupon.discount_type == 'FLAT':
            return min(self.coupon.discount_value, subtotal)
        elif self.coupon.discount_type == 'PERCENTAGE':
            return round(subtotal * self.coupon.discount_value / 100, 2)
        return 0

    def get_total(self):
        return self.get_subtotal() - self.get_discount()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cart', 'variant')

    def __str__(self):
        return f"{self.quantity}x {self.variant.sku} in {self.cart}"


class Order(models.Model):
    order_number = models.CharField(max_length=30, unique=True, editable=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='PENDING')
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)

    # Address snapshot
    shipping_name = models.CharField(max_length=150)
    shipping_phone = models.CharField(max_length=11)
    shipping_division = models.CharField(max_length=50)
    shipping_district = models.CharField(max_length=100)
    shipping_thana = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=10)
    shipping_full_address = models.TextField()

    tracking_note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = generate_order_number()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.order_number


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name='items')
    variant = models.ForeignKey(Variant, on_delete=models.PROTECT, null=True, blank=True)
    product_name = models.CharField(max_length=255)
    variant_sku = models.CharField(max_length=100)
    variant_attributes = models.JSONField(default=dict)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.quantity}x {self.variant_sku} in {self.order.order_number}"
