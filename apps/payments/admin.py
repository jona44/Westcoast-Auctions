from django.contrib import admin

from .models import PaymentRecord

@admin.register(PaymentRecord)
class PaymentRecordAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'listing', 'payment_type', 'amount', 'status', 'created_at')
    list_filter = ('status', 'payment_type', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'listing__title')
