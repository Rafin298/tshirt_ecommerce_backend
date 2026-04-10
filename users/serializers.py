from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Address

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'phone', 'full_name', 'password']

    def create(self, validated_data):
        return User.objects.create_user(
            email=validated_data['email'],
            phone=validated_data['phone'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
        )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'phone', 'full_name', 'date_joined']
        read_only_fields = ['id', 'email', 'date_joined']


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = [
            'id', 'label', 'recipient_name', 'phone',
            'division', 'district', 'thana', 'union',
            'postal_code', 'full_address', 'is_default', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']
