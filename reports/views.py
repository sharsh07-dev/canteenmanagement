from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.db.models import Sum, Count, Q, Avg, F
from django.utils import timezone
from billing.models import Order, OrderItem, Item, Category, Payment
import json
import datetime
import csv


def get_user_role(user):
    try:
        return user.profile.role
    except:
        return 'cashier'


def manager_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        role = get_user_role(request.user)
        if role not in ('admin', 'manager') and not request.user.is_superuser:
            from django.contrib import messages
            messages.error(request, "Access denied.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@manager_required
def sales_report(request):
    period = request.GET.get('period', 'daily')
    today = timezone.now().date()

    if period == 'daily':
        start_date = today
    elif period == 'weekly':
        start_date = today - datetime.timedelta(days=today.weekday())
    elif period == 'monthly':
        start_date = today.replace(day=1)
    elif period == 'custom':
        start_date = request.GET.get('start_date', str(today))
        end_date = request.GET.get('end_date', str(today))
        try:
            start_date = datetime.date.fromisoformat(start_date)
            end_date = datetime.date.fromisoformat(end_date)
        except:
            start_date = today
            end_date = today
    else:
        start_date = today

    if period != 'custom':
        end_date = today

    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status='completed'
    )

    summary = orders.aggregate(
        total_revenue=Sum('total_amount'),
        total_orders=Count('id'),
        total_tax=Sum('tax_amount'),
        total_discount=Sum('discount_amount'),
        avg_order=Avg('total_amount'),
    )

    # Payment method breakdown
    payment_breakdown = Payment.objects.filter(
        order__in=orders
    ).values('method').annotate(
        count=Count('id'),
        total=Sum('amount_paid'),
    )

    # Daily breakdown for chart
    date_range = []
    current = start_date
    while current <= end_date:
        date_range.append(current)
        current += datetime.timedelta(days=1)

    chart_labels = []
    chart_data = []
    for d in date_range[-30:]:  # max 30 points
        rev = orders.filter(created_at__date=d).aggregate(t=Sum('total_amount'))['t'] or 0
        chart_labels.append(d.strftime('%d %b'))
        chart_data.append(float(rev))

    # Top items
    top_items = OrderItem.objects.filter(order__in=orders).values(
        'item__name', 'item__category__name'
    ).annotate(
        total_qty=Sum('quantity'),
        total_rev=Sum(F('unit_price') * F('quantity')),
    ).order_by('-total_qty')[:10]

    context = {
        'period': period,
        'start_date': start_date,
        'end_date': end_date,
        'summary': summary,
        'payment_breakdown': list(payment_breakdown),
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'top_items': top_items,
        'orders': orders[:20],
    }
    return render(request, 'reports/sales_report.html', context)


@login_required
@manager_required
def export_csv(request):
    period = request.GET.get('period', 'daily')
    today = timezone.now().date()

    if period == 'daily':
        start_date = today
        end_date = today
    elif period == 'weekly':
        start_date = today - datetime.timedelta(days=today.weekday())
        end_date = today
    elif period == 'monthly':
        start_date = today.replace(day=1)
        end_date = today
    else:
        start_date = request.GET.get('start_date', str(today))
        end_date = request.GET.get('end_date', str(today))
        try:
            start_date = datetime.date.fromisoformat(start_date)
            end_date = datetime.date.fromisoformat(end_date)
        except:
            start_date = today
            end_date = today

    orders = Order.objects.filter(
        created_at__date__gte=start_date,
        created_at__date__lte=end_date,
        status='completed'
    ).select_related('cashier', 'payment')

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="sales_report_{period}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Order Number', 'Date', 'Cashier', 'Subtotal', 'Tax',
        'Discount', 'Total', 'Payment Method', 'Status'
    ])

    for order in orders:
        writer.writerow([
            order.order_number,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            order.cashier.username,
            order.subtotal,
            order.tax_amount,
            order.discount_amount,
            order.total_amount,
            order.payment.method if hasattr(order, 'payment') else 'N/A',
            order.status,
        ])

    return response


@login_required
@manager_required
def inventory_report(request):
    items = Item.objects.select_related('category').all()
    low_stock = [i for i in items if i.is_low_stock and i.is_active]
    out_of_stock = items.filter(stock_quantity=0)

    # Category stock summary
    category_summary = Category.objects.annotate(
        total_items=Count('items'),
        active_items=Count('items', filter=Q(items__is_active=True)),
        total_stock=Sum('items__stock_quantity'),
        total_value=Sum(F('items__stock_quantity') * F('items__cost_price')),
    )

    total_value = sum(
        (i.stock_quantity * i.cost_price) for i in items if i.is_active
    )

    return render(request, 'reports/inventory_report.html', {
        'items': items,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock,
        'category_summary': category_summary,
        'total_value': total_value,
    })
