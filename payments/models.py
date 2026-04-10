from django.db import models
from django.contrib.auth import get_user_model
from orders.models import Order

User = get_user_model()

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


class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name='payment')
    method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    bkash_number = models.CharField(max_length=11, blank=True, null=True)
    bkash_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    verified_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment for {self.order.order_number} ({self.method} - {self.status})"
