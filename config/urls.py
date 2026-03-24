from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    # Перемикач мови
    path('i18n/', include('django.conf.urls.i18n')),
]

# Всі URL з префіксом мови — /uk/ /en/ /de/ /fr/ /zh/
urlpatterns += i18n_patterns(
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('qr/', include('apps.qr_generator.urls')),
    path('accounts/', include('apps.accounts.urls')),
    path('payments/', include('apps.payments.urls')),
    prefix_default_language=False,  # /uk/ не додається для мови за замовч.
)

# Медіа файли локально (логотипи в QR кодах)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
