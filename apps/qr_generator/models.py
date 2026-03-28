from django.db import models
from django.utils import timezone
from apps.accounts.models import CustomUser
import uuid


class QRCode(models.Model):
    TYPE_CHOICES = [
        ('url', 'URL / Посилання'),
        ('text', 'Текст'),
        ('email', 'Email'),
        ('phone', 'Телефон'),
        ('wifi', 'Wi-Fi'),
        ('vcard', 'Контакт (vCard)'),
    ]

    STYLE_CHOICES = [
        ('square', 'Квадратний'),
        ('rounded', 'Заокруглений'),
        ('dots', 'Крапки'),
        ('diamonds', 'Діаманти'),
        ('stars', 'Зірки'),
        ('connected', 'З\'єднані'),
    ]

    EYE_STYLE_CHOICES = [
        ('square', 'Квадратні'),
        ('rounded', 'Округлі'),
        ('circle', 'Кола'),
        ('drop', 'Краплі'),
    ]

    FRAME_CHOICES = [
        ('none', 'Без рамки'),
        ('simple', 'Проста рамка'),
        ('scan_me', 'Скануй мене'),
        ('scan_me_en', 'Scan Me'),
    ]

    GRADIENT_CHOICES = [
        ('none', 'Без градієнту'),
        ('linear', 'Лінійний'),
        ('radial', 'Радіальний'),
    ]

    uid = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False,
        db_index=True
    )

    user = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='qr_codes',
        verbose_name='Користувач'
    )

    qr_type = models.CharField(
        max_length=16,
        choices=TYPE_CHOICES,
        default='url',
        verbose_name='Тип'
    )
    content = models.TextField(
        verbose_name='Вміст QR коду'
    )

    is_dynamic = models.BooleanField(
        default=False,
        verbose_name='Динамічний QR'
    )
    dynamic_url = models.URLField(
        blank=True,
        null=True,
        verbose_name='Динамічне посилання'
    )

    fg_color = models.CharField(
        max_length=7,
        default='#000000',
        verbose_name='Колір QR'
    )
    bg_color = models.CharField(
        max_length=7,
        default='#FFFFFF',
        verbose_name='Колір фону'
    )
    style = models.CharField(
        max_length=16,
        choices=STYLE_CHOICES,
        default='square',
        verbose_name='Стиль'
    )
    eye_style = models.CharField(
        max_length=16,
        choices=EYE_STYLE_CHOICES,
        default='square',
        verbose_name='Стиль очей'
    )
    frame = models.CharField(
        max_length=16,
        choices=FRAME_CHOICES,
        default='none',
        verbose_name='Рамка'
    )
    frame_text = models.CharField(
        max_length=32,
        blank=True,
        default='',
        verbose_name='Текст рамки'
    )
    gradient = models.CharField(
        max_length=16,
        choices=GRADIENT_CHOICES,
        default='none',
        verbose_name='Градієнт'
    )
    gradient_color = models.CharField(
        max_length=7,
        default='#000000',
        verbose_name='Другий колір градієнту'
    )
    logo = models.ImageField(
        upload_to='qr_logos/',
        blank=True,
        null=True,
        verbose_name='Логотип'
    )

    scan_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Кількість сканувань'
    )
    last_scanned_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Останнє сканування'
    )

    title = models.CharField(
        max_length=128,
        blank=True,
        verbose_name='Назва'
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'QR Код'
        verbose_name_plural = 'QR Коди'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_qr_type_display()} — {self.content[:40]}'

    def get_scan_url(self):
        return f'/qr/scan/{self.uid}/'

    def get_qr_content(self):
        if self.is_dynamic:
            return self.get_scan_url()
        return self.content


class QRScan(models.Model):
    qr_code = models.ForeignKey(
        QRCode,
        on_delete=models.CASCADE,
        related_name='scans',
        verbose_name='QR Код'
    )
    ip_address = models.GenericIPAddressField(
        blank=True,
        null=True,
        verbose_name='IP адреса'
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name='User Agent'
    )
    country = models.CharField(
        max_length=64,
        blank=True,
        verbose_name='Країна'
    )
    scanned_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = 'Сканування'
        verbose_name_plural = 'Сканування'
        ordering = ['-scanned_at']

    def __str__(self):
        return f'{self.qr_code} — {self.scanned_at}'
