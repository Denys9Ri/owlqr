from django.db import models
from django.utils import timezone
from apps.accounts.models import CustomUser


class Plan(models.Model):
    """Тарифні плани"""
    INTERVAL_CHOICES = [
        ('monthly', 'Щомісячно'),
        ('yearly', 'Щорічно'),
    ]

    name = models.CharField(max_length=64, verbose_name='Назва плану')
    interval = models.CharField(
        max_length=16,
        choices=INTERVAL_CHOICES,
        default='monthly',
        verbose_name='Інтервал'
    )
    price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Ціна'
    )
    currency = models.CharField(
        max_length=8,
        default='USD',
        verbose_name='Валюта'
    )
    is_active = models.BooleanField(default=True, verbose_name='Активний')
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'План'
        verbose_name_plural = 'Плани'

    def __str__(self):
        return f'{self.name} — {self.price} {self.currency}/{self.interval}'


class Subscription(models.Model):
    """Підписки користувачів"""
    STATUS_CHOICES = [
        ('active', 'Активна'),
        ('expired', 'Прострочена'),
        ('cancelled', 'Скасована'),
        ('pending', 'Очікує оплати'),
    ]

    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name='Користувач'
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        verbose_name='План'
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    paypal_order_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name='PayPal Order ID'
    )
    paypal_subscription_id = models.CharField(
        max_length=128,
        blank=True,
        null=True,
        verbose_name='PayPal Subscription ID'
    )
    started_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Початок підписки'
    )
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Кінець підписки'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Підписка'
        verbose_name_plural = 'Підписки'

    def __str__(self):
        return f'{self.user.email} — {self.plan.name} ({self.status})'

    @property
    def is_active(self):
        """Перевірка чи підписка активна"""
        if self.status != 'active':
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True

    def sync_user_premium(self):
        """Синхронізує is_premium користувача зі статусом підписки"""
        self.user.is_premium = self.is_active
        self.user.save(update_fields=['is_premium'])


class Payment(models.Model):
    """Історія платежів"""
    STATUS_CHOICES = [
        ('pending', 'Очікує'),
        ('completed', 'Виконано'),
        ('failed', 'Помилка'),
        ('refunded', 'Повернено'),
    ]

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Користувач'
    )
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='payments',
        verbose_name='Підписка'
    )
    paypal_order_id = models.CharField(
        max_length=128,
        verbose_name='PayPal Order ID'
    )
    amount = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        verbose_name='Сума'
    )
    currency = models.CharField(
        max_length=8,
        default='USD',
        verbose_name='Валюта'
    )
    status = models.CharField(
        max_length=16,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name='Статус'
    )
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Платіж'
        verbose_name_plural = 'Платежі'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.email} — {self.amount} {self.currency} ({self.status})'
