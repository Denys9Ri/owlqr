from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


def home_view(request):
    context = {
        'user': request.user,
    }
    return render(request, 'core/home.html', context)


def about_view(request):
    return render(request, 'core/about.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')
