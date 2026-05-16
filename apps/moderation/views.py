from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test, login_required
from django.contrib import messages
from django.utils import timezone
from .models import ListingApproval, ListingReport
from apps.auctions.models import Listing
from apps.accounts.models import Profile

def is_moderator(user):
    return user.is_staff or user.groups.filter(name='Moderators').exists()

@user_passes_test(is_moderator)
def moderation_queue(request):
    approvals = ListingApproval.objects.filter(status='pending').order_by('created_at')
    reports = ListingReport.objects.filter(is_reviewed=False).order_by('-created_at')
    all_listings = Listing.objects.all().order_by('-created_at')
    return render(request, 'moderation/queue.html', {
        'approvals': approvals,
        'reports': reports,
        'all_listings': all_listings
    })

@user_passes_test(is_moderator)
def force_delete_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        title = listing.title
        listing.delete()
        messages.success(request, f"Listing '{title}' has been forcefully deleted.")
    return redirect('moderation_queue')

@user_passes_test(is_moderator)
def approve_listing(request, pk):
    approval = get_object_or_404(ListingApproval, pk=pk)
    approval.status = 'approved'
    approval.moderator = request.user
    approval.reviewed_at = timezone.now()
    approval.save()
    
    # Ensure the listing is active
    approval.listing.is_active = True
    approval.listing.save()
    
    messages.success(request, f"Listing '{approval.listing.title}' has been approved.")
    return redirect('moderation_queue')

@user_passes_test(is_moderator)
def reject_listing(request, pk):
    approval = get_object_or_404(ListingApproval, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        approval.status = 'rejected'
        approval.moderator = request.user
        approval.rejection_reason = reason
        approval.reviewed_at = timezone.now()
        approval.save()
        
        # Deactivate the listing
        approval.listing.is_active = False
        approval.listing.save()
        
        messages.warning(request, f"Listing '{approval.listing.title}' has been rejected.")
        return redirect('moderation_queue')
    return render(request, 'moderation/reject_reason.html', {'approval': approval})

@login_required
def report_listing(request, pk):
    listing = get_object_or_404(Listing, pk=pk)
    if request.method == 'POST':
        reason = request.POST.get('reason')
        ListingReport.objects.create(
            listing=listing,
            user=request.user,
            reason=reason
        )
        messages.info(request, "Thank you for reporting. Our moderators will review this listing shortly.")
        return redirect('listing_detail', pk=pk)
    return render(request, 'moderation/report_form.html', {'listing': listing})

@user_passes_test(is_moderator)
def mark_report_reviewed(request, pk):
    report = get_object_or_404(ListingReport, pk=pk)
    report.is_reviewed = True
    report.save()
    messages.success(request, "Report marked as reviewed.")
    return redirect('moderation_queue')

@user_passes_test(is_moderator)
def verify_user(request, user_id):
    profile = get_object_or_404(Profile, user_id=user_id)
    profile.verified = True
    profile.save()
    messages.success(request, f"User '{profile.user.username}' is now a Verified Seller!")
    return redirect('moderation_queue')

@user_passes_test(is_moderator)
def ban_user(request, user_id):
    from apps.accounts.models import User
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    
    # Also deactivate all their listings
    Listing.objects.filter(seller=user).update(is_active=False)
    
    messages.error(request, f"User '{user.username}' has been banned and their listings deactivated.")
    return redirect('moderation_queue')
