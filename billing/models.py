from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#6366f1')  # hex color for UI
    icon = models.CharField(max_length=50, default='bi-grid')  # Bootstrap icon class
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Item(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='items')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.IntegerField(default=0)
    min_stock_level = models.IntegerField(default=5)  # low stock alert threshold
    barcode = models.CharField(max_length=100, blank=True, unique=True, null=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='items/', null=True, blank=True)
    is_active = models.BooleanField(default=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)  # percentage
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.min_stock_level

    @property
    def tax_amount_per_unit(self):
        return (self.price * self.tax_rate) / 100

    @property
    def price_with_tax(self):
        return self.price + self.tax_amount_per_unit

    class Meta:
        ordering = ['name']


class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    order_number = models.CharField(max_length=20, unique=True)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name='orders')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Order #{self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            import datetime
            now = datetime.datetime.now()
            prefix = now.strftime('%Y%m%d')
            last = Order.objects.filter(order_number__startswith=prefix).count()
            self.order_number = f"{prefix}{str(last + 1).zfill(4)}"
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item = models.ForeignKey(Item, on_delete=models.PROTECT, related_name='order_items')
    quantity = models.IntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    @property
    def subtotal(self):
        return self.unit_price * self.quantity

    @property
    def tax_amount(self):
        return (self.subtotal * self.tax_rate) / 100

    @property
    def total(self):
        return self.subtotal + self.tax_amount - self.discount

    def __str__(self):
        return f"{self.item.name} x {self.quantity}"


class Payment(models.Model):
    METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('wallet', 'Wallet'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='cash')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    change_given = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='completed')
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment for {self.order.order_number}"


class InventoryMovement(models.Model):
    TYPE_CHOICES = [
        ('in', 'Stock In'),
        ('out', 'Stock Out (Sale)'),
        ('adjustment', 'Manual Adjustment'),
        ('return', 'Return'),
        ('waste', 'Waste'),
    ]
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='movements')
    change_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    quantity = models.IntegerField()  # positive for in, negative for out
    previous_stock = models.IntegerField()
    new_stock = models.IntegerField()
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.item.name} - {self.change_type} ({self.quantity})"

    class Meta:
        ordering = ['-timestamp']
