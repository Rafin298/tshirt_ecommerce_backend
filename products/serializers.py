from rest_framework import serializers
from .models import Category, Product, ProductImage, Attribute, AttributeValue, Variant, VariantAttribute


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'parent', 'description', 'children']

    def get_children(self, obj):
        children = obj.children.filter(is_active=True)
        return CategorySerializer(children, many=True).data


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'is_primary', 'order']


class VariantAttributeSerializer(serializers.ModelSerializer):
    attribute = serializers.CharField(source='attribute_value.attribute.name')
    value = serializers.CharField(source='attribute_value.value')

    class Meta:
        model = VariantAttribute
        fields = ['attribute', 'value']


class VariantSerializer(serializers.ModelSerializer):
    attributes = serializers.SerializerMethodField()
    is_in_stock = serializers.BooleanField(read_only=True)

    class Meta:
        model = Variant
        fields = ['id', 'sku', 'price', 'stock_quantity', 'is_in_stock', 'is_active', 'attributes']

    def get_attributes(self, obj):
        va_qs = VariantAttribute.objects.filter(variant=obj).select_related('attribute_value__attribute')
        return [{'attribute': va.attribute_value.attribute.name, 'value': va.attribute_value.value} for va in va_qs]


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    primary_image = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    max_price = serializers.SerializerMethodField()
    is_in_stock = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'category', 'primary_image', 'min_price', 'max_price', 'is_in_stock']

    def get_primary_image(self, obj):
        img = obj.images.filter(is_primary=True).first()
        if img:
            request = self.context.get('request')
            return request.build_absolute_uri(img.image.url) if request else img.image.url
        return None

    def get_min_price(self, obj):
        prices = obj.variants.filter(is_active=True).values_list('price', flat=True)
        return min(prices) if prices else None

    def get_max_price(self, obj):
        prices = obj.variants.filter(is_active=True).values_list('price', flat=True)
        return max(prices) if prices else None

    def get_is_in_stock(self, obj):
        return obj.variants.filter(is_active=True, stock_quantity__gt=0).exists()


class ProductDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer()
    images = ProductImageSerializer(many=True)
    variants = VariantSerializer(many=True)

    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'description', 'category', 'images', 'variants', 'created_at', 'updated_at']
