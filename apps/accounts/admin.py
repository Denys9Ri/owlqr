from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    ordering = ['-created_at']
    list_display = [
        'email', 'first_name', 'last_name',
        'is_premium', 'is_staff', 'is_active', 'created_at'
    ]
    list_filter = ['is_premium', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    readonly_fields = ['created_at', 'updated_at', 'google_id']

    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Особисті дані'), {
            'fields': ('first_name', 'last_name', 'avatar_url')
        }),
        (_('Google OAuth'), {
            'fields': ('google_id',),
            'classes': ('collapse',)
        }),
        (_('Права доступу'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'is_premium', 'groups', 'user_permissions'
            )
        }),
        (_('Дати'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'first_name', 'last_name',
                'password1', 'password2',
                'is_staff', 'is_premium', 'is_active'
            ),
        }),
    )

    # Дозволяє адміну вручну давати/знімати premium
    actions = ['make_premium', 'remove_premium']

    @admin.action(description=_('Надати Premium'))
    def make_premium(self, request, queryset):
        queryset.update(is_premium=True)

    @admin.action(description=_('Зняти Premium'))
    def remove_premium(self, request, queryset):
        queryset.update(is_premium=False)
