import re
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    def create_user(self, email, phone, full_name, password=None, **extra_fields):
        if not email:
            raise ValueError('Email is required.')
        if not phone:
            raise ValueError('Phone is required.')
        email = self.normalize_email(email)
        user = self.model(email=email, phone=phone, full_name=full_name, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone, full_name, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, phone, full_name, password, **extra_fields)

BD_PHONE_REGEX = RegexValidator(
    regex=r'^01[3-9]\d{8}$',
    message="Enter a valid Bangladeshi phone number (01XXXXXXXXX)."
)

BD_DIVISIONS = [
    ('Dhaka', 'Dhaka'),
    ('Chittagong', 'Chittagong'),
    ('Rajshahi', 'Rajshahi'),
    ('Khulna', 'Khulna'),
    ('Barishal', 'Barishal'),
    ('Sylhet', 'Sylhet'),
    ('Rangpur', 'Rangpur'),
    ('Mymensingh', 'Mymensingh'),
]


class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=11, unique=True, validators=[BD_PHONE_REGEX])
    full_name = models.CharField(max_length=150)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone', 'full_name']

    objects = UserManager()

    def __str__(self):
        return self.email


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    label = models.CharField(max_length=50, help_text='e.g. Home, Office')
    recipient_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=11, validators=[BD_PHONE_REGEX])
    division = models.CharField(max_length=50, choices=BD_DIVISIONS)
    district = models.CharField(max_length=100)
    thana = models.CharField(max_length=100)
    union = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=10)
    full_address = models.TextField()
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.label} - {self.recipient_name} ({self.user.email})"
