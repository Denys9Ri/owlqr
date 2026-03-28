from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='QRCode',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('uid', models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True)),
                ('qr_type', models.CharField(choices=[('url', 'URL / Посилання'), ('text', 'Текст'), ('email', 'Email'), ('phone', 'Телефон'), ('wifi', 'Wi-Fi'), ('vcard', 'Контакт (vCard)')], default='url', max_length=16, verbose_name='Тип')),
                ('content', models.TextField(verbose_name='Вміст QR коду')),
                ('is_dynamic', models.BooleanField(default=False, verbose_name='Динамічний QR')),
                ('dynamic_url', models.URLField(blank=True, null=True, verbose_name='Динамічне посилання')),
                ('fg_color', models.CharField(default='#000000', max_length=7, verbose_name='Колір QR')),
                ('bg_color', models.CharField(default='#FFFFFF', max_length=7, verbose_name='Колір фону')),
                ('style', models.CharField(choices=[('square', 'Квадратний'), ('rounded', 'Заокруглений'), ('dots', 'Крапки')], default='square', max_length=16, verbose_name='Стиль')),
                ('logo', models.ImageField(blank=True, null=True, upload_to='qr_logos/', verbose_name='Логотип')),
                ('scan_count', models.PositiveIntegerField(default=0, verbose_name='Кількість сканувань')),
                ('last_scanned_at', models.DateTimeField(blank=True, null=True, verbose_name='Останнє сканування')),
                ('title', models.CharField(blank=True, max_length=128, verbose_name='Назва')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='qr_codes', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'QR Код',
                'verbose_name_plural': 'QR Коди',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='QRScan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP адреса')),
                ('user_agent', models.TextField(blank=True, verbose_name='User Agent')),
                ('country', models.CharField(blank=True, max_length=64, verbose_name='Країна')),
                ('scanned_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('qr_code', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='scans', to='qr_generator.qrcode', verbose_name='QR Код')),
            ],
            options={
                'verbose_name': 'Сканування',
                'verbose_name_plural': 'Сканування',
                'ordering': ['-scanned_at'],
            },
        ),
    ]
