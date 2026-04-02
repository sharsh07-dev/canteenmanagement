import os
import django
from decimal import Decimal

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'canteen.settings')
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from billing.models import Category, Item, InventoryMovement

def seed_data():
    print("Clearing existing data...")
    InventoryMovement.objects.all().delete()
    Item.objects.all().delete()
    Category.objects.all().delete()
    User.objects.filter(username__in=['admin', 'manager', 'cashier']).delete()

    print("Creating users...")
    admin_user = User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    admin_user.first_name = 'Admin'
    admin_user.last_name = 'User'
    admin_user.save()
    UserProfile.objects.create(user=admin_user, role='admin')

    manager = User.objects.create_user('manager', 'manager@example.com', 'manager123')
    manager.first_name = 'Store'
    manager.last_name = 'Manager'
    manager.save()
    UserProfile.objects.create(user=manager, role='manager')

    cashier = User.objects.create_user('cashier', 'cashier@example.com', 'cashier123')
    cashier.first_name = 'John'
    cashier.last_name = 'Cashier'
    cashier.save()
    UserProfile.objects.create(user=cashier, role='cashier')

    print("Creating categories...")
    categories_data = [
        {'name': 'Beverages', 'color': '#3b82f6', 'icon': 'bi-cup-hot', 'desc': 'Tea, Coffee, Cold drinks'},
        {'name': 'Snacks', 'color': '#f59e0b', 'icon': 'bi-cookie', 'desc': 'Chips, Biscuits, Samosa'},
        {'name': 'Meals', 'color': '#ef4444', 'icon': 'bi-shop', 'desc': 'Lunch and Dinner items'},
        {'name': 'Desserts', 'color': '#ec4899', 'icon': 'bi-cake', 'desc': 'Sweets and Ice cream'},
    ]
    
    categories = {}
    for c in categories_data:
        cat = Category.objects.create(
            name=c['name'], color=c['color'], icon=c['icon'], description=c['desc']
        )
        categories[c['name']] = cat

    print("Creating items...")
    items_data = [
        # Beverages
        {'name': 'Masala Chai', 'cat': 'Beverages', 'price': 15, 'cost': 8, 'stock': 100, 'barcode': '1001'},
        {'name': 'Filter Coffee', 'cat': 'Beverages', 'price': 25, 'cost': 12, 'stock': 80, 'barcode': '1002'},
        {'name': 'Cold Coffee', 'cat': 'Beverages', 'price': 45, 'cost': 20, 'stock': 50, 'barcode': '1003'},
        {'name': 'Coca Cola (250ml)', 'cat': 'Beverages', 'price': 20, 'cost': 15, 'stock': 120, 'barcode': '1004'},
        
        # Snacks
        {'name': 'Vegetable Samosa', 'cat': 'Snacks', 'price': 20, 'cost': 10, 'stock': 60, 'barcode': '2001'},
        {'name': 'Vada Pav', 'cat': 'Snacks', 'price': 25, 'cost': 12, 'stock': 55, 'barcode': '2002'},
        {'name': 'French Fries', 'cat': 'Snacks', 'price': 60, 'cost': 30, 'stock': 40, 'barcode': '2003'},
        {'name': 'Sandwich (Veg)', 'cat': 'Snacks', 'price': 45, 'cost': 25, 'stock': 30, 'barcode': '2004'},
        
        # Meals
        {'name': 'Veg Thali', 'cat': 'Meals', 'price': 120, 'cost': 70, 'stock': 40, 'barcode': '3001'},
        {'name': 'Chicken Biryani', 'cat': 'Meals', 'price': 150, 'cost': 90, 'stock': 25, 'barcode': '3002'},
        {'name': 'Paneer Butter Masala', 'cat': 'Meals', 'price': 110, 'cost': 60, 'stock': 35, 'barcode': '3003'},
        {'name': 'Roti', 'cat': 'Meals', 'price': 10, 'cost': 4, 'stock': 200, 'barcode': '3004'},
        
        # Desserts
        {'name': 'Gulab Jamun (2 pcs)', 'cat': 'Desserts', 'price': 40, 'cost': 20, 'stock': 45, 'barcode': '4001'},
        {'name': 'Vanilla Ice Cream', 'cat': 'Desserts', 'price': 35, 'cost': 18, 'stock': 60, 'barcode': '4002'},
        {'name': 'Chocolate Brownie', 'cat': 'Desserts', 'price': 70, 'cost': 35, 'stock': 20, 'barcode': '4003'},
    ]

    for item in items_data:
        i = Item.objects.create(
            name=item['name'],
            category=categories[item['cat']],
            price=Decimal(str(item['price'])),
            cost_price=Decimal(str(item['cost'])),
            stock_quantity=item['stock'],
            barcode=item['barcode'],
            tax_rate=Decimal('5.00')  # Default 5% tax
        )
        
        # Initial inventory movement
        InventoryMovement.objects.create(
            item=i,
            change_type='in',
            quantity=item['stock'],
            previous_stock=0,
            new_stock=item['stock'],
            performed_by=admin_user,
            notes='Initial seed data'
        )

    print("Seed data created successfully!")

if __name__ == '__main__':
    seed_data()
