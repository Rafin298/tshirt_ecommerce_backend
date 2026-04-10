from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product, Attribute, AttributeValue, Variant, VariantAttribute, StockMovement
from orders.models import Coupon
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed initial data: categories, attributes, sample product, and coupon'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # Categories
        clothing, _ = Category.objects.get_or_create(
            slug='clothing',
            defaults={'name': 'Clothing', 'is_active': True},
        )
        tshirts, _ = Category.objects.get_or_create(
            slug='t-shirts',
            defaults={'name': 'T-Shirts', 'parent': clothing, 'is_active': True},
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Categories: Clothing → T-Shirts'))

        # Attributes
        size_attr, _ = Attribute.objects.get_or_create(name='Size')
        color_attr, _ = Attribute.objects.get_or_create(name='Color')

        sizes = ['S', 'M', 'L', 'XL', 'XXL']
        colors = ['Black', 'White', 'Red', 'Navy', 'Green', 'Grey', 'Yellow']

        size_values = {}
        for s in sizes:
            val, _ = AttributeValue.objects.get_or_create(attribute=size_attr, value=s)
            size_values[s] = val

        color_values = {}
        for c in colors:
            val, _ = AttributeValue.objects.get_or_create(attribute=color_attr, value=c)
            color_values[c] = val

        self.stdout.write(self.style.SUCCESS('  ✓ Attributes: Size (S/M/L/XL/XXL), Color (7 colors)'))

        # Sample Product
        product, created = Product.objects.get_or_create(
            slug='classic-round-neck-tshirt',
            defaults={
                'name': 'Classic Round Neck T-Shirt',
                'description': 'A comfortable everyday round neck t-shirt made from 100% cotton. Available in multiple colors and sizes.',
                'category': tshirts,
                'is_active': True,
            }
        )

        if created:
            # Create 6 variants: 2 colors × 3 sizes (Black & White, L/XL/XXL)
            variant_combos = [
                ('Black', 'L',   'TSHIRT-BLK-L-001',   Decimal('450.00'), 20),
                ('Black', 'XL',  'TSHIRT-BLK-XL-001',  Decimal('480.00'), 15),
                ('Black', 'XXL', 'TSHIRT-BLK-XXL-001', Decimal('500.00'), 10),
                ('White', 'L',   'TSHIRT-WHT-L-001',   Decimal('450.00'), 20),
                ('White', 'XL',  'TSHIRT-WHT-XL-001',  Decimal('480.00'), 12),
                ('White', 'XXL', 'TSHIRT-WHT-XXL-001', Decimal('500.00'),  8),
            ]
            for color, size, sku, price, stock in variant_combos:
                variant = Variant.objects.create(
                    product=product,
                    sku=sku,
                    price=price,
                    stock_quantity=stock,
                    is_active=True,
                )
                VariantAttribute.objects.create(variant=variant, attribute_value=color_values[color])
                VariantAttribute.objects.create(variant=variant, attribute_value=size_values[size])
                StockMovement.objects.create(variant=variant, change=stock, reason='RESTOCK', note='Initial stock')

            self.stdout.write(self.style.SUCCESS('  ✓ Product: Classic Round Neck T-Shirt with 6 variants'))
        else:
            self.stdout.write('  - Product already exists, skipping variants.')

        # Coupon
        coupon, created = Coupon.objects.get_or_create(
            code='WELCOME100',
            defaults={
                'discount_type': 'FLAT',
                'discount_value': Decimal('100.00'),
                'min_order_value': Decimal('500.00'),
                'is_active': True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS('  ✓ Coupon: WELCOME100 (BDT 100 off, min order BDT 500)'))
        else:
            self.stdout.write('  - Coupon WELCOME100 already exists.')

        self.stdout.write(self.style.SUCCESS('\nSeed complete!'))
