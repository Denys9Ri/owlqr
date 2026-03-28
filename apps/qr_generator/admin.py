from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from .models import QRCode, QRScan


@admin.register(QRCode)
class QRCodeAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'qr_type', 'title',
        'is_dynamic', 'scan_count', 'created_at'
    ]
    list_filter = ['qr_type', 'is_dynamic', 'style']
    search_fields = ['user__email', 'content', 'title']
    readonly_fields = [
        'uid', 'scan_count', 'last_scanned_at',
        'created_at', 'updated_at'
    ]
    ordering = ['-created_at']

    fieldsets = (
        (None, {
            'fields': ('uid', 'user', 'title', 'qr_type', 'content')
        }),
        (_('Динамічний QR'), {
            'fields': ('is_dynamic', 'dynamic_url'),
            'classes': ('collapse',)
        }),
        (_('Дизайн'), {
            'fields': ('fg_color', 'bg_color', 'style', 'logo'),
            'classes': ('collapse',)
        }),
        (_('Статистика'), {
            'fields': ('scan_count', 'last_scanned_at')
        }),
        (_('Дати'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['reset_scan_count']

    @admin.action(description=_('Скинути лічильник сканувань'))
    def reset_scan_count(self, request, queryset):
        queryset.update(scan_count=0)


@admin.register(QRScan)
class QRScanAdmin(admin.ModelAdmin):
    list_display = [
        'qr_code', 'ip_address', 'country', 'scanned_at'
    ]
    list_filter = ['country', 'scanned_at']
    search_fields = ['qr_code__title', 'ip_address', 'country']
    readonly_fields = [
        'qr_code', 'ip_address', 'user_agent',
        'country', 'scanned_at'
    ]
    ordering = ['-scanned_at']

    # Тільки перегляд — скани не редагуємо
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
