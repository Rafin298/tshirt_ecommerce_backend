from django.urls import path
from users.views import (
    UserProfileView, AddressListCreateView,
    AddressDetailView, SetDefaultAddressView,
)

urlpatterns = [
    path('me/', UserProfileView.as_view(), name='user-profile'),
    path('addresses/', AddressListCreateView.as_view(), name='address-list-create'),
    path('addresses/<int:pk>/', AddressDetailView.as_view(), name='address-detail'),
    path('addresses/<int:pk>/set-default/', SetDefaultAddressView.as_view(), name='address-set-default'),
]
