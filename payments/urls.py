from django.urls import path
from .views import CODPaymentView, BkashSubmitView, PaymentStatusView

urlpatterns = [
    path('cod/', CODPaymentView.as_view(), name='payment-cod'),
    path('bkash/submit/', BkashSubmitView.as_view(), name='payment-bkash-submit'),
    path('<str:order_number>/status/', PaymentStatusView.as_view(), name='payment-status'),
]
