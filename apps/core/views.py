from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def home_view(request):
    qr_types = [
        ('🔗', _('Посилання / URL')),
        ('📝', _('Текст')),
        ('📧', _('Email')),
        ('📞', _('Телефон')),
        ('📶', _('Wi-Fi')),
        ('👤', _('Контакт vCard')),
    ]
    return render(request, 'core/home.html', {
        'user': request.user,
        'qr_types': qr_types,
    })


def about_view(request):
    return render(request, 'core/about.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')
