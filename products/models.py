from django.db import models
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from PIL import Image


def validate_image(image):
    if image.size > 5 * 1024 * 1024:
        raise ValidationError("Image must be under 5MB.")
    if not image.name.lower().endswith(('.jpg', '.jpeg', '.png')):
        raise ValidationError("Only JPG and PNG images are allowed.")


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/', validators=[validate_image])
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)
        # Auto-compress
        img = Image.open(self.image.path)
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        if img.width > 1000:
            ratio = 1000 / img.width
            new_height = int(img.height * ratio)
            img = img.resize((1000, new_height), Image.LANCZOS)
        img.save(self.image.path, format='JPEG', quality=75, optimize=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class Attribute(models.Model):
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=100)

    class Meta:
        unique_together = ('attribute', 'value')

    def __str__(self):
        return f"{self.attribute.name}: {self.value}"


class Variant(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    sku = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    attributes = models.ManyToManyField(AttributeValue, through='VariantAttribute', related_name='variants')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0

    def __str__(self):
        return f"{self.product.name} - {self.sku}"


class VariantAttribute(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    attribute_value = models.ForeignKey(AttributeValue, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('variant', 'attribute_value')


STOCK_REASON_CHOICES = [
    ('RESTOCK', 'Restock'),
    ('SALE', 'Sale'),
    ('CANCELLATION', 'Cancellation'),
    ('ADJUSTMENT', 'Adjustment'),
]


class StockMovement(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='stock_movements')
    change = models.IntegerField(help_text='Positive = added, Negative = deducted')
    reason = models.CharField(max_length=20, choices=STOCK_REASON_CHOICES)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.variant.sku}: {self.change} ({self.reason})"
