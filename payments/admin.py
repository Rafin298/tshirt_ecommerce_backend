from django.contrib import admin
from django.utils import timezone
from .models import Payment
from orders.models import Order


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['order', 'method', 'amount', 'status', 'bkash_transaction_id', 'verified_by', 'created_at']
    list_filter = ['method', 'status']
    search_fields = ['order__order_number', 'bkash_transaction_id', 'bkash_number']
    readonly_fields = ['order', 'method', 'amount', 'bkash_number', 'bkash_transaction_id', 'created_at', 'verified_by', 'verified_at']
    fields = [
        'order', 'method', 'amount', 'status',
        'bkash_number', 'bkash_transaction_id',
        'verified_by', 'verified_at', 'note', 'created_at',
    ]
    actions = ['mark_collected', 'mark_verified', 'mark_failed']

    def mark_collected(self, request, queryset):
        queryset.filter(method='COD', status='PENDING').update(status='COLLECTED')
        # Update order payment_status
        for payment in queryset.filter(method='COD'):
            payment.order.payment_status = 'COLLECTED'
            payment.order.save()
    mark_collected.short_description = 'Mark COD payments as COLLECTED'

    def mark_verified(self, request, queryset):
        for payment in queryset.filter(method='BKASH', status='PENDING'):
            payment.status = 'VERIFIED'
            payment.verified_by = request.user
            payment.verified_at = timezone.now()
            payment.save()
            payment.order.payment_status = 'VERIFIED'
            payment.order.status = 'CONFIRMED'
            payment.order.save()
    mark_verified.short_description = 'Mark bKash payments as VERIFIED (auto-confirms order)'

    def mark_failed(self, request, queryset):
        queryset.filter(method='BKASH', status='PENDING').update(status='FAILED')
        for payment in queryset.filter(method='BKASH'):
            payment.order.payment_status = 'FAILED'
            payment.order.save()
    mark_failed.short_description = 'Mark bKash payments as FAILED'
