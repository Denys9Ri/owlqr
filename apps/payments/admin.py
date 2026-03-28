from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import Plan, Subscription, Payment


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'interval', 'price', 'currency', 'is_active']
    list_filter = ['interval', 'is_active', 'currency']
    search_fields = ['name']
    list_editable = ['price', 'is_active']
    ordering = ['price']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'plan', 'status',
        'started_at', 'expires_at', 'updated_at'
    ]
    list_filter = ['status', 'plan']
    search_fields = ['user__email', 'paypal_order_id', 'paypal_subscription_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('user', 'plan', 'status')
        }),
        (_('PayPal'), {
            'fields': ('paypal_order_id', 'paypal_subscription_id'),
            'classes': ('collapse',)
        }),
        (_('Дати'), {
            'fields': ('started_at', 'expires_at', 'created_at', 'updated_at')
        }),
    )

    # Дозволяє вручну активувати/деактивувати підписку
    actions = ['activate_subscription', 'expire_subscription']

    @admin.action(description=_('Активувати підписку'))
    def activate_subscription(self, request, queryset):
        for sub in queryset:
            sub.status = 'active'
            sub.save()
            sub.sync_user_premium()

    @admin.action(description=_('Деактивувати підписку'))
    def expire_subscription(self, request, queryset):
        for sub in queryset:
            sub.status = 'expired'
            sub.save()
            sub.sync_user_premium()


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'amount', 'currency',
        'status', 'paypal_order_id', 'created_at'
    ]
    list_filter = ['status', 'currency']
    search_fields = ['user__email', 'paypal_order_id']
    readonly_fields = ['created_at']
    ordering = ['-created_at']

    # Тільки перегляд — платежі не редагуємо
    def has_change_permission(self, request, obj=None):
        return False
