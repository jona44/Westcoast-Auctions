from django import forms
from .models import Listing, Bid


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultipleFileField(forms.FileField):
    """A FileField that accepts multiple files and never errors when empty."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("required", False)
        super().__init__(*args, **kwargs)
        self.widget = MultipleFileInput(attrs={"multiple": True})

    def clean(self, data, initial=None):
        # data can be a list (multiple files), a single file, or an empty value
        if not data:
            if self.required:
                raise forms.ValidationError(self.error_messages["required"])
            return []
        # Normalise to a list
        if not isinstance(data, (list, tuple)):
            data = [data]
        results = []
        for item in data:
            # Skip the empty sentinel Django sends when no file is chosen
            if not item:
                continue
            validated = super().clean(item, initial)
            # Reject non-image files with a friendly error
            content_type = getattr(item, "content_type", "") or ""
            if not content_type.startswith("image/"):
                raise forms.ValidationError(
                    f"'{item.name}' is not a valid image file. "
                    "Please upload only images (JPEG, PNG, WebP, etc.)."
                )
            results.append(validated)
        return results


class ListingForm(forms.ModelForm):
    additional_images = MultipleFileField(required=False)
    start_time = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    )
    end_time = forms.DateTimeField(
        widget=forms.DateTimeInput(format='%Y-%m-%dT%H:%M', attrs={'type': 'datetime-local'}),
        input_formats=['%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%d %H:%M:%S']
    )

    class Meta:
        model = Listing
        fields = ['title', 'description', 'starting_bid', 'category', 'deposit_required', 'deposit_amount', 'image', 'additional_images', 'start_time', 'end_time']
        widgets = {
            'description': forms.Textarea(attrs={'rows': '3'}),
        }
    
    field_order = ['title', 'description', 'starting_bid', 'category', 'deposit_required', 'deposit_amount', 'image', 'additional_images', 'start_time', 'end_time']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].required = False
        self.fields['additional_images'].required = False
        self.fields['deposit_amount'].required = False
        self.fields['deposit_amount'].help_text = 'Optional deposit amount required before bidding.'
        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class': 'block w-full px-4 py-3 rounded-xl border border-slate-200 focus:ring-2 focus:ring-blue-600 focus:border-transparent transition-all outline-none bg-slate-50'
            })

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        deposit_required = cleaned_data.get('deposit_required')
        deposit_amount = cleaned_data.get('deposit_amount')

        if start_time and end_time and start_time >= end_time:
            self.add_error('end_time', "End time must be after the start time.")

        if deposit_required:
            if not deposit_amount or deposit_amount <= 0:
                self.add_error('deposit_amount', "Deposit amount must be set and greater than zero when a deposit is required.")
            elif deposit_amount >= cleaned_data.get('starting_bid', 0):
                self.add_error('deposit_amount', "Deposit amount should be less than the starting bid.")

        return cleaned_data

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']
        
    def __init__(self, *args, **kwargs):
        self.listing = kwargs.pop('listing', None)
        super().__init__(*args, **kwargs)
        self.fields['amount'].widget.attrs.update({
            'class': 'w-full pl-12 pr-4 py-5 rounded-2xl border-2 border-slate-100 focus:border-blue-600 focus:ring-4 focus:ring-blue-100 transition-all outline-none bg-slate-50 font-bold text-lg',
            'placeholder': f'Higher than ${self.listing.current_bid if self.listing else "0.00"}'
        })

    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if self.listing and amount <= self.listing.current_bid:
            raise forms.ValidationError(f"Your bid must be higher than the current bid (${self.listing.current_bid})")
        return amount
