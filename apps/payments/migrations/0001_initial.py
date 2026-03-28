from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Plan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=64, verbose_name='Назва плану')),
                ('interval', models.CharField(choices=[('monthly', 'Щомісячно'), ('yearly', 'Щорічно')], default='monthly', max_length=16, verbose_name='Інтервал')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Ціна')),
                ('currency', models.CharField(default='USD', max_length=8, verbose_name='Валюта')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активний')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
            ],
            options={
                'verbose_name': 'План',
                'verbose_name_plural': 'Плани',
            },
        ),
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('active', 'Активна'), ('expired', 'Прострочена'), ('cancelled', 'Скасована'), ('pending', 'Очікує оплати')], default='pending', max_length=16, verbose_name='Статус')),
                ('paypal_order_id', models.CharField(blank=True, max_length=128, null=True, verbose_name='PayPal Order ID')),
                ('paypal_subscription_id', models.CharField(blank=True, max_length=128, null=True, verbose_name='PayPal Subscription ID')),
                ('started_at', models.DateTimeField(blank=True, null=True, verbose_name='Початок підписки')),
                ('expires_at', models.DateTimeField(blank=True, null=True, verbose_name='Кінець підписки')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='payments.plan', verbose_name='План')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscription', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Підписка',
                'verbose_name_plural': 'Підписки',
            },
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('paypal_order_id', models.CharField(max_length=128, verbose_name='PayPal Order ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Сума')),
                ('currency', models.CharField(default='USD', max_length=8, verbose_name='Валюта')),
                ('status', models.CharField(choices=[('pending', 'Очікує'), ('completed', 'Виконано'), ('failed', 'Помилка'), ('refunded', 'Повернено')], default='pending', max_length=16, verbose_name='Статус')),
                ('created_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('subscription', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payments', to='payments.subscription', verbose_name='Підписка')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='payments', to=settings.AUTH_USER_MODEL, verbose_name='Користувач')),
            ],
            options={
                'verbose_name': 'Платіж',
                'verbose_name_plural': 'Платежі',
                'ordering': ['-created_at'],
            },
        ),
    ]
