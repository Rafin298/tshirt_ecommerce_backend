from django.urls import path
from .views import (
    CartView, CartAddView, CartItemUpdateView, CartClearView,
    ApplyCouponView, PlaceOrderView, OrderListView, OrderDetailView, CancelOrderView,
)

urlpatterns = [
    path('cart/', CartView.as_view(), name='cart'),
    path('cart/add/', CartAddView.as_view(), name='cart-add'),
    path('cart/items/<int:pk>/', CartItemUpdateView.as_view(), name='cart-item-update'),
    path('cart/clear/', CartClearView.as_view(), name='cart-clear'),
    path('cart/apply-coupon/', ApplyCouponView.as_view(), name='cart-apply-coupon'),
    path('cart/remove-coupon/', ApplyCouponView.as_view(), name='cart-remove-coupon'),
    path('orders/', OrderListView.as_view(), name='order-list'),
    path('orders/place/', PlaceOrderView.as_view(), name='order-place'),
    path('orders/<str:order_number>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<str:order_number>/cancel/', CancelOrderView.as_view(), name='order-cancel'),
]
