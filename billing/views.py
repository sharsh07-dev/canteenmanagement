from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Sum, Count, Q, F
from django.db import models
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
import json
import datetime
from decimal import Decimal

from billing.models import (
    Item, Category, Order, OrderItem, Payment, InventoryMovement
)
from accounts.models import UserProfile


def get_user_role(user):
    try:
        return user.profile.role
    except:
        return 'cashier'


def role_required(*roles):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('login')
            role = get_user_role(request.user)
            if role not in roles and not request.user.is_superuser:
                messages.error(request, "You don't have permission to access this page.")
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


@login_required
def dashboard(request):
    today = timezone.now().date()
    week_start = today - datetime.timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Today's stats
    today_orders = Order.objects.filter(created_at__date=today, status='completed')
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    today_count = today_orders.count()

    # Weekly stats
    week_orders = Order.objects.filter(created_at__date__gte=week_start, status='completed')
    week_revenue = week_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    # Monthly stats
    month_orders = Order.objects.filter(created_at__date__gte=month_start, status='completed')
    month_revenue = month_orders.aggregate(total=Sum('total_amount'))['total'] or 0

    # Low stock items
    low_stock_items = Item.objects.filter(
        stock_quantity__lte=models.F('min_stock_level'),
        is_active=True
    )[:5]

    # Top selling items (last 30 days)
    thirty_days_ago = today - datetime.timedelta(days=30)
    top_items = OrderItem.objects.filter(
        order__created_at__date__gte=thirty_days_ago,
        order__status='completed'
    ).values('item__name').annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum('unit_price')
    ).order_by('-total_qty')[:5]

    # Recent orders
    recent_orders = Order.objects.all()[:8]

    # Sales chart data (last 7 days)
    chart_labels = []
    chart_data = []
    for i in range(6, -1, -1):
        date = today - datetime.timedelta(days=i)
        rev = Order.objects.filter(
            created_at__date=date, status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        chart_labels.append(date.strftime('%d %b'))
        chart_data.append(float(rev))

    # Category distribution
    category_data = Category.objects.annotate(
        item_count=Count('items', filter=Q(items__is_active=True))
    ).values('name', 'item_count', 'color')

    context = {
        'today_revenue': today_revenue,
        'today_count': today_count,
        'week_revenue': week_revenue,
        'month_revenue': month_revenue,
        'low_stock_items': low_stock_items,
        'top_items': top_items,
        'recent_orders': recent_orders,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'category_data': json.dumps(list(category_data)),
        'total_items': Item.objects.filter(is_active=True).count(),
        'total_users': User.objects.count(),
        'low_stock_count': Item.objects.filter(
            stock_quantity__lte=models.F('min_stock_level'), is_active=True
        ).count(),
    }
    return render(request, 'billing/dashboard.html', context)


@login_required
def pos(request):
    """POS Billing Interface"""
    categories = Category.objects.filter(is_active=True).prefetch_related('items')
    items = Item.objects.filter(is_active=True, stock_quantity__gt=0).select_related('category')
    return render(request, 'billing/pos.html', {
        'categories': categories,
        'items': items,
    })


@login_required
@csrf_exempt
def create_order(request):
    """API endpoint to create a new order"""
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        cart = data.get('cart', [])
        payment_method = data.get('payment_method', 'cash')
        amount_paid = Decimal(str(data.get('amount_paid', 0)))
        discount = Decimal(str(data.get('discount', 0)))
        notes = data.get('notes', '')

        if not cart:
            return JsonResponse({'error': 'Cart is empty'}, status=400)

        # Calculate totals
        subtotal = Decimal('0')
        tax_total = Decimal('0')
        order_items_data = []

        for cart_item in cart:
            item = get_object_or_404(Item, id=cart_item['id'], is_active=True)
            qty = int(cart_item['quantity'])

            if item.stock_quantity < qty:
                return JsonResponse({
                    'error': f'Insufficient stock for {item.name}. Available: {item.stock_quantity}'
                }, status=400)

            item_subtotal = item.price * qty
            item_tax = (item_subtotal * item.tax_rate) / 100
            subtotal += item_subtotal
            tax_total += item_tax
            order_items_data.append({
                'item': item,
                'quantity': qty,
                'unit_price': item.price,
                'tax_rate': item.tax_rate,
            })

        total = subtotal + tax_total - discount
        change = amount_paid - total if amount_paid > total else Decimal('0')

        # Create order
        order = Order.objects.create(
            cashier=request.user,
            subtotal=subtotal,
            tax_amount=tax_total,
            discount_amount=discount,
            total_amount=total,
            notes=notes,
            status='completed',
        )

        # Create order items and update inventory
        for oi_data in order_items_data:
            item = oi_data['item']
            qty = oi_data['quantity']
            prev_stock = item.stock_quantity

            OrderItem.objects.create(
                order=order,
                item=item,
                quantity=qty,
                unit_price=oi_data['unit_price'],
                tax_rate=oi_data['tax_rate'],
            )

            # Deduct stock
            item.stock_quantity -= qty
            item.save()

            # Record inventory movement
            InventoryMovement.objects.create(
                item=item,
                change_type='out',
                quantity=-qty,
                previous_stock=prev_stock,
                new_stock=item.stock_quantity,
                order=order,
                performed_by=request.user,
            )

        # Create payment
        Payment.objects.create(
            order=order,
            method=payment_method,
            amount_paid=amount_paid,
            change_given=change,
            status='completed',
        )

        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'order_number': order.order_number,
            'total': float(total),
            'change': float(change),
            'redirect': f'/billing/receipt/{order.id}/',
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def receipt(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'billing/receipt.html', {'order': order})


@login_required
def order_list(request):
    orders = Order.objects.all().select_related('cashier', 'payment')
    q = request.GET.get('q', '')
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) | Q(cashier__username__icontains=q)
        )

    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)

    date_from = request.GET.get('date_from', '')
    if date_from:
        orders = orders.filter(created_at__date__gte=date_from)
    date_to = request.GET.get('date_to', '')
    if date_to:
        orders = orders.filter(created_at__date__lte=date_to)

    paginator = Paginator(orders, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'billing/order_list.html', {
        'page_obj': page_obj,
        'q': q,
        'status_filter': status_filter,
    })


@login_required
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'billing/order_detail.html', {'order': order})


@login_required
def get_items_api(request):
    """API to get items for POS search"""
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')

    items = Item.objects.filter(is_active=True, stock_quantity__gt=0)
    if q:
        items = items.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
    if category_id:
        items = items.filter(category_id=category_id)

    data = [{
        'id': item.id,
        'name': item.name,
        'price': float(item.price),
        'tax_rate': float(item.tax_rate),
        'stock': item.stock_quantity,
        'category': item.category.name,
        'barcode': item.barcode or '',
    } for item in items[:50]]

    return JsonResponse({'items': data})


# Import missing models reference
from django.db import models as django_models
from billing.models import Item
