from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm, UserUpdateForm, ProfileForm, PhoneVerificationForm
from .models import Profile
from .sms import create_phone_otp, verify_phone_code

def register_view(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            try:
                create_phone_otp(user)
            except Exception as exc:
                messages.error(request, 'Failed to send verification SMS. Please try again later.')
                user.delete()
                return render(request, 'accounts/register.html', {'form': form})

            login(request, user)
            messages.success(request, 'Account created. A verification code has been sent to your phone.')
            return redirect('verify_phone')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect('listing_list')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def verify_phone(request):
    if request.user.phone_verified:
        messages.info(request, 'Your phone number is already verified.')
        return redirect('profile')

    if request.method == 'POST':
        form = PhoneVerificationForm(request.POST)
        if form.is_valid():
            if verify_phone_code(request.user, form.cleaned_data['code']):
                messages.success(request, 'Phone number successfully verified.')
                return redirect('profile')
            messages.error(request, 'Invalid or expired verification code. Please try again.')
    else:
        form = PhoneVerificationForm()

    return render(request, 'accounts/verify_phone.html', {'form': form})

@login_required
def resend_phone_verification(request):
    if not request.user.phone_number:
        messages.error(request, 'Add a phone number to your account before requesting a new code.')
        return redirect('profile')

    try:
        create_phone_otp(request.user)
        messages.success(request, 'A new verification code has been sent to your phone.')
    except Exception:
        messages.error(request, 'Unable to send verification SMS right now. Please try again later.')
    return redirect('verify_phone')

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('listing_list')

from apps.auctions.models import Listing

@login_required
def profile_view(request):
    user_listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
    
    if request.method == 'POST':
        old_phone = request.user.phone_number
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        
        if u_form.is_valid() and p_form.is_valid():
            user = u_form.save(commit=False)
            if user.phone_number != old_phone:
                user.phone_verified = False
            user.save()
            p_form.save()
            if user.phone_number != old_phone and user.phone_number:
                try:
                    create_phone_otp(user)
                    messages.info(request, 'Phone number updated. A new verification code has been sent.')
                except Exception:
                    messages.error(request, 'Failed to send new verification code. Please try again later.')
            else:
                messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileForm(instance=request.user.profile)
        
    return render(request, 'accounts/profile.html', {
        'u_form': u_form,
        'p_form': p_form,
        'user_listings': user_listings
    })
