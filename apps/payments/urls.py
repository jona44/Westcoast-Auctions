from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:pk>/', views.checkout_view, name='checkout'),
    path('itn/', views.payfast_itn_view, name='payfast_itn'),
    path('success/', views.payment_success_view, name='payment_success'),
    path('cancel/', views.payment_cancel_view, name='payment_cancel'),
]