from django.contrib import admin

from .models import User, Profile
from django.contrib.auth.admin import UserAdmin

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_seller', 'is_buyer', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('is_seller', 'is_buyer', 'phone_number', 'bio')}),
    )

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'country', 'verified')
    list_filter = ('verified', 'country')
    search_fields = ('user__username', 'city', 'country')
