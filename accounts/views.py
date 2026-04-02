from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from accounts.models import UserProfile


@login_required
def user_list(request):
    try:
        role = request.user.profile.role
    except:
        role = 'cashier'

    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    users = User.objects.select_related('profile').all()
    return render(request, 'accounts/user_list.html', {'users': users})


@login_required
def user_create(request):
    try:
        role = request.user.profile.role
    except:
        role = 'cashier'

    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        user_role = request.POST.get('role', 'cashier')
        phone = request.POST.get('phone', '').strip()

        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
        else:
            user = User.objects.create_user(
                username=username,
                password=password,
                first_name=first_name,
                last_name=last_name,
                email=email,
            )
            UserProfile.objects.create(user=user, role=user_role, phone=phone)
            messages.success(request, f'User "{username}" created successfully.')
            return redirect('user_list')

    return render(request, 'accounts/user_form.html', {'action': 'Create'})


@login_required
def user_edit(request, user_id):
    try:
        role = request.user.profile.role
    except:
        role = 'cashier'

    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    target_user = get_object_or_404(User, id=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    if request.method == 'POST':
        target_user.first_name = request.POST.get('first_name', '').strip()
        target_user.last_name = request.POST.get('last_name', '').strip()
        target_user.email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '').strip()
        if new_password:
            target_user.set_password(new_password)
        target_user.save()

        profile.role = request.POST.get('role', profile.role)
        profile.phone = request.POST.get('phone', '').strip()
        profile.save()

        messages.success(request, f'User "{target_user.username}" updated.')
        return redirect('user_list')

    return render(request, 'accounts/user_form.html', {
        'target_user': target_user,
        'profile': profile,
        'action': 'Edit',
    })


@login_required
def user_delete(request, user_id):
    try:
        role = request.user.profile.role
    except:
        role = 'cashier'

    if role != 'admin' and not request.user.is_superuser:
        messages.error(request, "Admin access required.")
        return redirect('dashboard')

    target_user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        if target_user == request.user:
            messages.error(request, "You cannot delete your own account.")
        else:
            username = target_user.username
            target_user.is_active = False
            target_user.save()
            messages.success(request, f'User "{username}" deactivated.')
    return redirect('user_list')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next', 'dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'accounts/login.html')

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Username and password are required.')
        elif User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
        else:
            user = User.objects.create_user(
                username=username,
                first_name=first_name,
                password=password
            )
            UserProfile.objects.create(user=user, role='cashier')
            messages.success(request, 'Account created! Please log in.')
            return redirect('login')

    return render(request, 'accounts/signup.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def profile_view(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        new_password = request.POST.get('password', '').strip()
        if new_password:
            request.user.set_password(new_password)
        request.user.save()
        profile.phone = request.POST.get('phone', '').strip()
        profile.save()
        messages.success(request, 'Profile updated successfully.')
        return redirect('profile')
    return render(request, 'accounts/profile.html', {'profile': profile})
