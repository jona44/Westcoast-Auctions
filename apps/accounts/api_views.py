from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import CustomUserSerializer, FCMDeviceSerializer, UserRegistrationSerializer
from .models import User, FCMDevice
from .sms import create_phone_otp, verify_phone_code
from .forms import RegisterForm

class CurrentUserView(generics.RetrieveAPIView):
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

from .serializers import CustomUserSerializer, UserRegistrationSerializer, MyTokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class MyTokenObtainPairView(TokenObtainPairView):
    serializer_class = MyTokenObtainPairSerializer

class UserRegistrationView(generics.CreateAPIView):
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            try:
                create_phone_otp(user)
            except Exception:
                return Response({'detail': 'Failed to send verification SMS.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(CustomUserSerializer(user).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class FCMDeviceView(generics.CreateAPIView):
    serializer_class = FCMDeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            FCMDevice.objects.get_or_create(
                user=request.user,
                token=serializer.validated_data['token']
            )
            return Response({'status': 'Device registered'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RequestPhoneOTPView(APIView):
    """Send a fresh OTP to the authenticated user's phone number."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        phone = request.data.get('phone_number', '').strip()

        if phone:
            # Allow updating phone number if not yet verified
            if not user.phone_verified:
                user.phone_number = phone
                user.save(update_fields=['phone_number'])

        if not user.phone_number:
            return Response(
                {'error': 'No phone number on your account. Please provide one.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if user.phone_verified:
            return Response({'detail': 'Phone already verified.'}, status=status.HTTP_200_OK)

        try:
            create_phone_otp(user)
        except Exception as e:
            return Response(
                {'error': f'Failed to send verification SMS: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            {'detail': 'OTP sent successfully.', 'phone_number': user.phone_number},
            status=status.HTTP_200_OK
        )


class VerifyPhoneOTPView(APIView):
    """Verify the OTP code submitted by the user."""
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = request.data.get('code', '').strip()
        if not code:
            return Response({'error': 'OTP code is required.'}, status=status.HTTP_400_BAD_REQUEST)

        success = verify_phone_code(request.user, code)
        if success:
            return Response({'detail': 'Phone verified successfully.', 'phone_verified': True})
        return Response(
            {'error': 'Invalid or expired code. Please try again.'},
            status=status.HTTP_400_BAD_REQUEST
        )
