from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Sum
from django.db import models
from django.core.paginator import Paginator
from billing.models import Item, Category, InventoryMovement
from accounts.models import UserProfile


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
            messages.error(request, "Access denied. Manager or Admin role required.")
            return redirect('dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@manager_required
def item_list(request):
    items = Item.objects.select_related('category').all()
    q = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    stock_filter = request.GET.get('stock', '')

    if q:
        items = items.filter(Q(name__icontains=q) | Q(barcode__icontains=q))
    if category_id:
        items = items.filter(category_id=category_id)
    if stock_filter == 'low':
        items = [i for i in items if i.is_low_stock]
    elif stock_filter == 'out':
        items = items.filter(stock_quantity=0)

    categories = Category.objects.filter(is_active=True)
    paginator = Paginator(items, 20)
    page_obj = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'inventory/item_list.html', {
        'page_obj': page_obj,
        'categories': categories,
        'q': q,
        'category_id': category_id,
        'stock_filter': stock_filter,
    })


@login_required
@manager_required
def item_create(request):
    categories = Category.objects.filter(is_active=True)
    if request.method == 'POST':
        try:
            name = request.POST.get('name', '').strip()
            if not name:
                messages.error(request, 'Item name is required.')
                return render(request, 'inventory/item_form.html', {'categories': categories})

            item = Item(
                name=name,
                category_id=request.POST.get('category'),
                price=request.POST.get('price', 0),
                cost_price=request.POST.get('cost_price', 0),
                stock_quantity=request.POST.get('stock_quantity', 0),
                min_stock_level=request.POST.get('min_stock_level', 5),
                tax_rate=request.POST.get('tax_rate', 0),
                description=request.POST.get('description', ''),
                barcode=request.POST.get('barcode', '') or None,
                is_active=request.POST.get('is_active') == 'on',
            )
            if 'image' in request.FILES:
                item.image = request.FILES['image']
            item.save()

            # Record initial stock movement
            if item.stock_quantity > 0:
                InventoryMovement.objects.create(
                    item=item,
                    change_type='in',
                    quantity=item.stock_quantity,
                    previous_stock=0,
                    new_stock=item.stock_quantity,
                    performed_by=request.user,
                    notes='Initial stock entry',
                )

            messages.success(request, f'Item "{item.name}" created successfully.')
            return redirect('item_list')
        except Exception as e:
            messages.error(request, f'Error creating item: {e}')

    return render(request, 'inventory/item_form.html', {'categories': categories, 'action': 'Create'})


@login_required
@manager_required
def item_edit(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    categories = Category.objects.filter(is_active=True)

    if request.method == 'POST':
        try:
            old_stock = item.stock_quantity
            item.name = request.POST.get('name', item.name).strip()
            item.category_id = request.POST.get('category', item.category_id)
            item.price = request.POST.get('price', item.price)
            item.cost_price = request.POST.get('cost_price', item.cost_price)
            item.stock_quantity = int(request.POST.get('stock_quantity', item.stock_quantity))
            item.min_stock_level = request.POST.get('min_stock_level', item.min_stock_level)
            item.tax_rate = request.POST.get('tax_rate', item.tax_rate)
            item.description = request.POST.get('description', '')
            item.barcode = request.POST.get('barcode', '') or None
            item.is_active = request.POST.get('is_active') == 'on'
            if 'image' in request.FILES:
                item.image = request.FILES['image']
            item.save()

            # Record stock adjustment if changed
            new_stock = item.stock_quantity
            if old_stock != new_stock:
                diff = new_stock - old_stock
                InventoryMovement.objects.create(
                    item=item,
                    change_type='adjustment',
                    quantity=diff,
                    previous_stock=old_stock,
                    new_stock=new_stock,
                    performed_by=request.user,
                    notes='Manual stock adjustment via edit',
                )

            messages.success(request, f'Item "{item.name}" updated successfully.')
            return redirect('item_list')
        except Exception as e:
            messages.error(request, f'Error updating item: {e}')

    return render(request, 'inventory/item_form.html', {
        'item': item,
        'categories': categories,
        'action': 'Edit',
    })


@login_required
@manager_required
def item_delete(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        item.is_active = False
        item.save()
        messages.success(request, f'Item "{item.name}" deactivated.')
    return redirect('item_list')


@login_required
@manager_required
def category_list(request):
    categories = Category.objects.annotate(item_count=models.Count('items'))
    return render(request, 'inventory/category_list.html', {'categories': categories})


@login_required
@manager_required
def category_create(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        if not name:
            messages.error(request, 'Category name is required.')
        else:
            cat = Category.objects.create(
                name=name,
                description=request.POST.get('description', ''),
                color=request.POST.get('color', '#6366f1'),
                icon=request.POST.get('icon', 'bi-grid'),
            )
            messages.success(request, f'Category "{cat.name}" created.')
            return redirect('category_list')
    return render(request, 'inventory/category_form.html', {'action': 'Create'})


@login_required
@manager_required
def category_edit(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        cat.name = request.POST.get('name', cat.name).strip()
        cat.description = request.POST.get('description', '')
        cat.color = request.POST.get('color', '#6366f1')
        cat.icon = request.POST.get('icon', 'bi-grid')
        cat.save()
        messages.success(request, f'Category "{cat.name}" updated.')
        return redirect('category_list')
    return render(request, 'inventory/category_form.html', {'category': cat, 'action': 'Edit'})


@login_required
@manager_required
def category_delete(request, cat_id):
    cat = get_object_or_404(Category, id=cat_id)
    if request.method == 'POST':
        cat.is_active = False
        cat.save()
        messages.success(request, f'Category "{cat.name}" deactivated.')
    return redirect('category_list')


@login_required
@manager_required
def stock_adjust(request, item_id):
    item = get_object_or_404(Item, id=item_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 0))
        change_type = request.POST.get('change_type', 'adjustment')
        notes = request.POST.get('notes', '')
        old_stock = item.stock_quantity
        item.stock_quantity += quantity
        item.save()
        InventoryMovement.objects.create(
            item=item,
            change_type=change_type,
            quantity=quantity,
            previous_stock=old_stock,
            new_stock=item.stock_quantity,
            performed_by=request.user,
            notes=notes,
        )
        messages.success(request, f'Stock adjusted for {item.name}.')
        return redirect('item_list')
    return render(request, 'inventory/stock_adjust.html', {'item': item})


@login_required
@manager_required
def movement_history(request):
    movements = InventoryMovement.objects.select_related('item', 'performed_by', 'order').all()
    item_id = request.GET.get('item', '')
    if item_id:
        movements = movements.filter(item_id=item_id)
    paginator = Paginator(movements, 25)
    page_obj = paginator.get_page(request.GET.get('page', 1))
    items = Item.objects.filter(is_active=True)
    return render(request, 'inventory/movement_history.html', {
        'page_obj': page_obj,
        'items': items,
        'item_id': item_id,
    })


from django.db import models
