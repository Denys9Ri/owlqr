import json
import os
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from dateutil.relativedelta import relativedelta
from .models import Plan, Subscription, Payment


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
        # Передаємо Client ID у шаблон для JS
        'paypal_client_id': os.getenv('PAYPAL_CLIENT_ID', ''), 
    })


# ─── Успішна оплата (приймає сигнал від JS) ───────────────
@login_required
def paypal_success_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            subscription_id = data.get('subscription_id')
            plan_id = data.get('plan_id')

            plan = get_object_or_404(Plan, id=plan_id, is_active=True)

            if not subscription_id:
                return JsonResponse({'status': 'error', 'message': 'No subscription ID'}, status=400)

            now = timezone.now()
            if plan.interval == 'monthly':
                expires_at = now + relativedelta(months=1)
            else:
                expires_at = now + relativedelta(years=1)

            # Оновлюємо або створюємо підписку в БД
            subscription, created = Subscription.objects.update_or_create(
                user=request.user,
                defaults={
                    'plan': plan,
                    'status': 'active',
                    'paypal_order_id': subscription_id, # зберігаємо ID підписки PayPal
                    'started_at': now,
                    'expires_at': expires_at,
                }
            )

            # Фіксуємо платіж
            Payment.objects.create(
                user=request.user,
                subscription=subscription,
                paypal_order_id=subscription_id,
                amount=plan.price,
                currency=plan.currency,
                status='completed',
            )

            # Вмикаємо юзеру PRO
            if hasattr(subscription, 'sync_user_premium'):
                subscription.sync_user_premium()
            else:
                request.user.is_premium = True
                request.user.save()

            messages.success(request, _('Підписку активовано! Ласкаво просимо до OwlQR Pro!'))
            return JsonResponse({'status': 'success'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=400)
            
    return JsonResponse({'status': 'error', 'message': 'Invalid request'}, status=400)


# ─── Скасування підписки ──────────────────────────────────
@login_required
def cancel_subscription_view(request):
    subscription = Subscription.objects.filter(user=request.user).first()

    if not subscription:
        messages.error(request, _('Підписку не знайдено'))
        return redirect('accounts:profile')

    subscription.status = 'cancelled'
    subscription.save()
    if hasattr(subscription, 'sync_user_premium'):
        subscription.sync_user_premium()

    messages.success(request, _('Підписку скасовано'))
    return redirect('accounts:profile')
