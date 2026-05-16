from django.contrib import admin

from .models import ListingApproval, ListingReport

@admin.register(ListingApproval)
class ListingApprovalAdmin(admin.ModelAdmin):
    list_display = ('listing', 'status', 'moderator', 'reviewed_at', 'created_at')
    list_filter = ('status',)
    search_fields = ('listing__title', 'moderator__username')

@admin.register(ListingReport)
class ListingReportAdmin(admin.ModelAdmin):
    list_display = ('listing', 'user', 'is_reviewed', 'created_at')
    list_filter = ('is_reviewed',)
    search_fields = ('listing__title', 'user__username', 'reason')
