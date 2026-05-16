from django.urls import path
from . import views

urlpatterns = [
    path('queue/', views.moderation_queue, name='moderation_queue'),
    path('approve/<int:pk>/', views.approve_listing, name='approve_listing'),
    path('reject/<int:pk>/', views.reject_listing, name='reject_listing'),
    path('report/<int:pk>/', views.report_listing, name='report_listing'),
    path('report/<int:pk>/reviewed/', views.mark_report_reviewed, name='mark_report_reviewed'),
    path('user/<int:user_id>/verify/', views.verify_user, name='verify_user'),
    path('user/<int:user_id>/ban/', views.ban_user, name='ban_user'),
    path('listing/<int:pk>/force-delete/', views.force_delete_listing, name='force_delete_listing'),
]
