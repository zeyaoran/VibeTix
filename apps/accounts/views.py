from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from .forms import UserRegisterForm, UserLoginForm, UserProfileForm
from .models import User


@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Role.CUSTOMER
            user.save()
            login(request, user)
            messages.success(request, f"Welcome to VibeTix, {user.username}! Your account has been registered successfully.")
            return redirect('core:home')
    else:
        form = UserRegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    next_url = request.GET.get('next', request.POST.get('next', ''))

    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.cleaned_data.get('user')
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            if next_url and not next_url.startswith('//') and not '://' in next_url:
                return redirect(next_url)
            return redirect('core:home')
    else:
        form = UserLoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.info(request, "You have been safely logged out.")
    return redirect('accounts:login')


@login_required
@require_http_methods(["GET", "POST"])
def profile_view(request):
    """
    Authenticated user profile view and edit.
    Allows editing first_name, last_name, email, phone_number, and avatar.
    """
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been successfully updated.")
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)

    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'accounts/profile.html', context)
