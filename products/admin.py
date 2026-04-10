from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Product, ProductImage, Attribute, AttributeValue, Variant, VariantAttribute, StockMovement


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'created_at']
    list_filter = ['is_active', 'parent']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'is_primary', 'order', 'image_preview']
    readonly_fields = ['image_preview']

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height:80px;" />', obj.image.url)
        return '-'


class VariantAttributeInline(admin.TabularInline):
    model = VariantAttribute
    extra = 1


class VariantInline(admin.TabularInline):
    model = Variant
    extra = 0
    fields = ['sku', 'price', 'stock_quantity', 'is_active']


class StockMovementInline(admin.TabularInline):
    model = StockMovement
    extra = 0
    readonly_fields = ['variant', 'change', 'reason', 'note', 'created_at']

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'variant_count', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [ProductImageInline, VariantInline]
    actions = ['activate_products', 'deactivate_products']

    def variant_count(self, obj):
        return obj.variants.count()
    variant_count.short_description = 'Variants'

    def activate_products(self, request, queryset):
        queryset.update(is_active=True)
    activate_products.short_description = 'Activate selected products'

    def deactivate_products(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_products.short_description = 'Deactivate selected products'


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value']
    list_filter = ['attribute']


@admin.register(Variant)
class VariantAdmin(admin.ModelAdmin):
    list_display = ['sku', 'product', 'price', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'product__category']
    search_fields = ['sku', 'product__name']
    inlines = [VariantAttributeInline, StockMovementInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ['variant', 'change', 'reason', 'created_at']
    list_filter = ['reason']
    readonly_fields = ['variant', 'change', 'reason', 'note', 'created_at']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
