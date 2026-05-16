from django.urls import path
from . import views, api_views
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('verify-phone/', views.verify_phone, name='verify_phone'),
    path('verify-phone/resend/', views.resend_phone_verification, name='resend_phone_verification'),
    
    # API Endpoints
    path('api/register/', api_views.UserRegistrationView.as_view(), name='api_register'),
    path('api/token/', api_views.MyTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/me/', api_views.CurrentUserView.as_view(), name='api_me'),
    path('api/fcm-token/', api_views.FCMDeviceView.as_view(), name='api_fcm_token'),
    path('api/request-otp/', api_views.RequestPhoneOTPView.as_view(), name='api_request_otp'),
    path('api/verify-otp/', api_views.VerifyPhoneOTPView.as_view(), name='api_verify_otp'),
]

