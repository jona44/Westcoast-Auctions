from rest_framework import serializers
from .models import User, Profile, FCMDevice
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.db.models import Q

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['avatar', 'address', 'city', 'country', 'verified']

class FCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = FCMDevice
        fields = ['token']

class CustomUserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone_number', 'phone_verified', 'bio', 'is_seller', 'is_buyer', 'profile']

class UserRegistrationSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'phone_number', 'is_seller', 'is_buyer')

    def validate_phone_number(self, value):
        phone = value.strip()
        if not phone:
            raise serializers.ValidationError('Phone number is required for verification.')
        if not phone.lstrip('+').isdigit() or len(phone) < 9:
            raise serializers.ValidationError('Enter a valid phone number including country code.')
        return phone

    def validate(self, data):
        if data['password1'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password1')
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user

class MyTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        # Allow login with either username or email
        login_id = attrs.get('username')
        password = attrs.get('password')

        if login_id:
            user = User.objects.filter(Q(username=login_id) | Q(email=login_id)).first()
            if user and user.check_password(password):
                # Update username to the actual username for simple_jwt internal use
                attrs['username'] = user.username
            else:
                # If we custom-filtered, we need to fail here if no user found
                # Or we can let the super().validate handle the standard username login
                pass

        return super().validate(attrs)

