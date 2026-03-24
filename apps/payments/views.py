import os
import requests
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from .models import Plan, Subscription, Payment


# ─── Отримання PayPal Access Token ────────────────────────
def get_paypal_access_token():
    client_id = os.getenv('PAYPAL_CLIENT_ID')
    client_secret = os.getenv('PAYPAL_CLIENT_SECRET')
    mode = os.getenv('PAYPAL_MODE', 'sandbox')

    if mode == 'sandbox':
        url = 'https://api-m.sandbox.paypal.com/v1/oauth2/token'
    else:
        url = 'https://api-m.paypal.com/v1/oauth2/token'

    response = requests.post(
        url,
        headers={'Accept': 'application/json'},
        auth=(client_id, client_secret),
        data={'grant_type': 'client_credentials'}
    )
    return response.json().get('access_token')


# ─── Базовий PayPal URL ────────────────────────────────────
def get_paypal_base_url():
    mode = os.getenv('PAYPAL_MODE', 'sandbox')
    if mode == 'sandbox':
        return 'https://api-m.sandbox.paypal.com'
    return 'https://api-m.paypal.com'


# ─── Сторінка тарифів ─────────────────────────────────────
def pricing_view(request):
    plans = Plan.objects.filter(is_active=True).order_by('price')
    user_subscription = None

    if request.user.is_authenticated:
        user_subscription = Subscription.objects.filter(
            user=request.user
        ).first()

    return render(request, 'payments/pricing.html', {
        'plans': plans,
        'user_subscription': user_subscription,
    })


# ─── Створення PayPal замовлення ──────────────────────────
@login_required
def create_order_view(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    access_token = get_paypal_access_token()

    order_data = {
        'intent': 'CAPTURE',
        'purchase_units': [{
            'amount': {
                'currency_code': plan.currency,
                'value': str(plan.price),
            },
            'description': f'OwlQR {plan.name} — {plan.interval}',
        }],
        'application_context': {
            'brand_name': 'OwlQR',
            'return_url': request.build_absolute_uri(f'/payments/success/{plan_id}/'),
            'cancel_url': request.build_absolute_uri('/payments/cancel/'),
            'user_action': 'PAY_NOW',
        }
    }

    response = requests.post(
        f'{get_paypal_base_url()}/v2/checkout/orders',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        },
        json=order_data
    )
    order = response.json()

    if response.status_code != 201:
        messages.error(request, _('Помилка створення платежу. Спробуйте ще раз.'))
        return redirect('payments:pricing')

    # Зберігаємо order_id в сесії
    request.session['paypal_order_id'] = order.get('id')
    request.session['plan_id'] = plan_id

    # Перенаправляємо на PayPal
    for link in order.get('links', []):
        if link.get('rel') == 'approve':
            return redirect(link.get('href'))

    messages.error(request, _('Не вдалось отримати посилання PayPal'))
    return redirect('payments:pricing')


# ─── Успішна оплата ───────────────────────────────────────
@login_required
def payment_success_view(request, plan_id):
    order_id = request.GET.get('token')
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)

    if not order_id:
        messages.error(request, _('Помилка підтвердження платежу'))
        return redirect('payments:pricing')

    # Підтверджуємо платіж у PayPal
    access_token = get_paypal_access_token()
    response = requests.post(
        f'{get_paypal_base_url()}/v2/checkout/orders/{order_id}/capture',
        headers={
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json',
        }
    )
    capture_data = response.json()

    if capture_data.get('status') != 'COMPLETED':
        messages.error(request, _('Платіж не підтверджено'))
        return redirect('payments:pricing')

    # Визначаємо дату закінчення підписки
    now = timezone.now()
    if plan.interval == 'monthly':
        expires_at = now + relativedelta(months=1)
    else:
        expires_at = now + relativedelta(years=1)

    # Створюємо або оновлюємо підписку
    subscription, created = Subscription.objects.update_or_create(
        user=request.user,
        defaults={
            'plan': plan,
            'status': 'active',
            'paypal_order_id': order_id,
            'started_at': now,
            'expires_at': expires_at,
        }
    )

    # Зберігаємо платіж в історії
    Payment.objects.create(
        user=request.user,
        subscription=subscription,
        paypal_order_id=order_id,
        amount=plan.price,
        currency=plan.currency,
        status='completed',
    )

    # Оновлюємо is_premium користувача
    subscription.sync_user_premium()

    # Очищаємо сесію
    request.session.pop('paypal_order_id', None)
    request.session.pop('plan_id', None)

    messages.success(request, _('Підписку активовано! Ласкаво просимо до OwlQR Pro!'))
    return redirect('accounts:profile')


# ─── Скасування оплати ────────────────────────────────────
@login_required
def payment_cancel_view(request):
    messages.warning(request, _('Оплату скасовано'))
    return redirect('payments:pricing')


# ─── Скасування підписки ──────────────────────────────────
@login_required
def cancel_subscription_view(request):
    subscription = Subscription.objects.filter(user=request.user).first()

    if not subscription:
        messages.error(request, _('Підписку не знайдено'))
        return redirect('accounts:profile')

    subscription.status = 'cancelled'
    subscription.save()
    subscription.sync_user_premium()

    messages.success(request, _('Підписку скасовано'))
    return redirect('accounts:profile')
