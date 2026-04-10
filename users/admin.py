from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Address


class AddressInline(admin.TabularInline):
    model = Address
    extra = 0
    fields = ['label', 'recipient_name', 'phone', 'division', 'district', 'thana', 'postal_code', 'is_default']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ['-date_joined']
    list_display = ['email', 'phone', 'full_name', 'is_active', 'date_joined']
    list_filter = ['is_active', 'date_joined']
    search_fields = ['email', 'phone', 'full_name']
    inlines = [AddressInline]
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('full_name', 'phone')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'full_name', 'password1', 'password2'),
        }),
    )


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'label', 'recipient_name', 'division', 'district', 'is_default']
    list_filter = ['division', 'is_default']
    search_fields = ['user__email', 'recipient_name', 'phone']
