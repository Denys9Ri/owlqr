from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('', views.pricing_view, name='pricing'),
    path('order/<int:plan_id>/', views.create_order_view, name='create_order'),
    path('success/<int:plan_id>/', views.payment_success_view, name='success'),
    path('cancel/', views.payment_cancel_view, name='cancel'),
    path('cancel-subscription/', views.cancel_subscription_view, name='cancel_subscription'),
]
