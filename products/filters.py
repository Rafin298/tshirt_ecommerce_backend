import django_filters
from .models import Product


class ProductFilter(django_filters.FilterSet):
    category = django_filters.CharFilter(field_name='category__slug', lookup_expr='exact')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    min_price = django_filters.NumberFilter(method='filter_min_price')
    max_price = django_filters.NumberFilter(method='filter_max_price')

    class Meta:
        model = Product
        fields = ['category', 'in_stock', 'min_price', 'max_price']

    def filter_in_stock(self, queryset, name, value):
        if value:
            return queryset.filter(variants__stock_quantity__gt=0, variants__is_active=True).distinct()
        return queryset

    def filter_min_price(self, queryset, name, value):
        return queryset.filter(variants__price__gte=value, variants__is_active=True).distinct()

    def filter_max_price(self, queryset, name, value):
        return queryset.filter(variants__price__lte=value, variants__is_active=True).distinct()
