from django.core.management.base import BaseCommand
from django.utils.text import slugify
from products.models import Category, Product, Attribute, AttributeValue, Variant, VariantAttribute, StockMovement
from orders.models import Coupon
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed initial data: categories, size attribute, 6 products with size variants, and coupon'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # --------------------
        # Categories
        # --------------------
        clothing, _ = Category.objects.get_or_create(
            slug='clothing',
            defaults={'name': 'Clothing', 'is_active': True},
        )

        tshirts, _ = Category.objects.get_or_create(
            slug='t-shirts',
            defaults={'name': 'T-Shirts', 'parent': clothing, 'is_active': True},
        )

        self.stdout.write(self.style.SUCCESS('✓ Categories created'))

        # --------------------
        # Size Attribute only
        # --------------------
        size_attr, _ = Attribute.objects.get_or_create(name='Size')

        sizes = ['S', 'M', 'L', 'XL', 'XXL']

        size_values = {}
        for s in sizes:
            val, _ = AttributeValue.objects.get_or_create(
                attribute=size_attr,
                value=s
            )
            size_values[s] = val

        self.stdout.write(self.style.SUCCESS('✓ Size attribute created'))

        # --------------------
        # Product list
        # --------------------
        products_data = [
            {
                "name": "Classic Round Neck T-Shirt",
                "sizes": ["M", "L", "XL"]
            },
            {
                "name": "Oversized Streetwear T-Shirt",
                "sizes": ["L", "XL", "XXL"]
            },
            {
                "name": "Minimal Logo T-Shirt",
                "sizes": ["S", "M", "L", "XL"]
            },
            {
                "name": "Premium Cotton T-Shirt",
                "sizes": ["M", "L", "XL", "XXL"]
            },
            {
                "name": "Summer Lightweight T-Shirt",
                "sizes": ["S", "M", "L"]
            },
            {
                "name": "Heavyweight Gym T-Shirt",
                "sizes": ["M", "L", "XL"]
            },
        ]

        base_price = Decimal("450.00")

        for product_data in products_data:

            slug = slugify(product_data["name"])

            product, created = Product.objects.get_or_create(
                slug=slug,
                defaults={
                    "name": product_data["name"],
                    "description": f"{product_data['name']} made from comfortable cotton fabric.",
                    "category": tshirts,
                    "is_active": True,
                }
            )

            if created:

                for size in product_data["sizes"]:

                    price = base_price

                    if size == "XL":
                        price += Decimal("20")

                    elif size == "XXL":
                        price += Decimal("40")

                    sku = f"{slug[:8].upper()}-{size}-001"

                    variant = Variant.objects.create(
                        product=product,
                        sku=sku,
                        price=price,
                        stock_quantity=20,
                        is_active=True,
                    )

                    VariantAttribute.objects.create(
                        variant=variant,
                        attribute_value=size_values[size]
                    )

                    StockMovement.objects.create(
                        variant=variant,
                        change=20,
                        reason="RESTOCK",
                        note="Initial stock"
                    )

                self.stdout.write(
                    self.style.SUCCESS(f"✓ Created product: {product.name}")
                )

            else:
                self.stdout.write(f"- Product exists: {product.name}")

        # --------------------
        # Coupon
        # --------------------
        coupon, created = Coupon.objects.get_or_create(
            code="WELCOME100",
            defaults={
                "discount_type": "FLAT",
                "discount_value": Decimal("100.00"),
                "min_order_value": Decimal("500.00"),
                "is_active": True,
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS("✓ Coupon WELCOME100 created"))
        else:
            self.stdout.write("- Coupon already exists")

        self.stdout.write(self.style.SUCCESS("\nSEED COMPLETE"))