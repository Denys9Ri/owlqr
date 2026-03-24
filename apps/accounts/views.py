import os
import json
import requests
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


# ─── Реєстрація ───────────────────────────────────────────
def register_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password1 = request.POST.get('password1', '')
        password2 = request.POST.get('password2', '')
        first_name = request.POST.get('first_name', '').strip()

        # Валідація
        if not email or not password1 or not password2:
            messages.error(request, _('Заповніть всі поля'))
            return render(request, 'accounts/register.html')

        if password1 != password2:
            messages.error(request, _('Паролі не співпадають'))
            return render(request, 'accounts/register.html')

        if len(password1) < 8:
            messages.error(request, _('Пароль має бути мінімум 8 символів'))
            return render(request, 'accounts/register.html')

        if CustomUser.objects.filter(email=email).exists():
            messages.error(request, _('Цей email вже зареєстрований'))
            return render(request, 'accounts/register.html')

        # Створення користувача
        user = CustomUser.objects.create_user(
            email=email,
            password=password1,
            first_name=first_name,
        )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, _('Ласкаво просимо до OwlQR!'))
        return redirect('core:home')

    return render(request, 'accounts/register.html')


# ─── Логін ────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect('core:home')

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, _('Заповніть всі поля'))
            return render(request, 'accounts/login.html')

        user = authenticate(request, username=email, password=password)

        if user is not None:
            if user.is_active:
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                next_url = request.GET.get('next', '/')
                return redirect(next_url)
            else:
                messages.error(request, _('Акаунт деактивовано'))
        else:
            messages.error(request, _('Невірний email або пароль'))

    return render(request, 'accounts/login.html')


# ─── Логаут ───────────────────────────────────────────────
def logout_view(request):
    logout(request)
    return redirect('core:home')


# ─── Профіль ──────────────────────────────────────────────
@login_required
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        user.first_name = first_name
        user.last_name = last_name
        user.save()
        messages.success(request, _('Профіль оновлено'))
        return redirect('accounts:profile')

    return render(request, 'accounts/profile.html', {'user': user})


# ─── Google OAuth ─────────────────────────────────────────
def google_login_view(request):
    google_client_id = os.getenv('GOOGLE_CLIENT_ID')
    redirect_uri = request.build_absolute_uri('/accounts/google/callback/')
    scope = 'openid email profile'
    auth_url = (
        f'https://accounts.google.com/o/oauth2/v2/auth'
        f'?client_id={google_client_id}'
        f'&redirect_uri={redirect_uri}'
        f'&response_type=code'
        f'&scope={scope}'
        f'&access_type=offline'
    )
    return redirect(auth_url)


def google_callback_view(request):
    code = request.GET.get('code')
    if not code:
        messages.error(request, _('Помилка авторизації через Google'))
        return redirect('accounts:login')

    # Обмін коду на токен
    token_url = 'https://oauth2.googleapis.com/token'
    token_data = {
        'code': code,
        'client_id': os.getenv('GOOGLE_CLIENT_ID'),
        'client_secret': os.getenv('GOOGLE_CLIENT_SECRET'),
        'redirect_uri': request.build_absolute_uri('/accounts/google/callback/'),
        'grant_type': 'authorization_code',
    }
    token_response = requests.post(token_url, data=token_data)
    token_json = token_response.json()

    if 'error' in token_json:
        messages.error(request, _('Помилка отримання токену Google'))
        return redirect('accounts:login')

    # Отримання даних користувача
    access_token = token_json.get('access_token')
    user_info_response = requests.get(
        'https://www.googleapis.com/oauth2/v2/userinfo',
        headers={'Authorization': f'Bearer {access_token}'}
    )
    user_info = user_info_response.json()

    google_id = user_info.get('id')
    email = user_info.get('email', '').lower()
    first_name = user_info.get('given_name', '')
    last_name = user_info.get('family_name', '')
    avatar_url = user_info.get('picture', '')

    if not email:
        messages.error(request, _('Не вдалось отримати email від Google'))
        return redirect('accounts:login')

    # Знайти або створити користувача
    user, created = CustomUser.objects.get_or_create(
        email=email,
        defaults={
            'google_id': google_id,
            'first_name': first_name,
            'last_name': last_name,
            'avatar_url': avatar_url,
            'is_active': True,
        }
    )

    # Якщо користувач вже є — оновлюємо Google дані
    if not created:
        user.google_id = google_id
        user.avatar_url = avatar_url
        user.save()

    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    messages.success(request, _('Ласкаво просимо до OwlQR!'))
    return redirect('core:home')
