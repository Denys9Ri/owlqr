from django.urls import path
from . import views

app_name = 'qr_generator'

urlpatterns = [
    path('', views.generator_view, name='generator'),
    path('my/', views.my_qr_codes_view, name='my_qr_codes'),
    path('download/<int:qr_id>/', views.download_qr_view, name='download'),
    path('delete/<int:qr_id>/', views.delete_qr_view, name='delete'),
    path('edit/<int:qr_id>/', views.edit_dynamic_url_view, name='edit_dynamic'),
    path('scan/<uuid:uid>/', views.dynamic_redirect_view, name='dynamic_redirect'),
]
