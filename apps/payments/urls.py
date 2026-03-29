from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.pricing_view, name='pricing'),
    path('paypal-success/', views.paypal_success_view, name='paypal_success'),
    path('cancel-subscription/', views.cancel_subscription_view, name='cancel_subscription'),
]
