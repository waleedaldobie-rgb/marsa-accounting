from django import forms
from .models import WasteAdjustment


class WasteAdjustmentForm(forms.ModelForm):
    class Meta:
        model = WasteAdjustment
        fields = ['branch', 'location', 'product', 'quantity', 'waste_type', 'processing_record', 'reason']
        widgets = {
            'quantity': forms.NumberInput(attrs={'step': '0.001', 'min': '0.001'}),
            'reason': forms.Textarea(attrs={'rows': 3, 'placeholder': 'اذكر سبب الهدر بوضوح'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser and user.branch_id:
            self.fields['branch'].queryset = self.fields['branch'].queryset.filter(pk=user.branch_id)
            self.fields['location'].queryset = self.fields['location'].queryset.filter(branch_id=user.branch_id)
            self.fields['branch'].initial = user.branch_id
            self.fields['location'].initial = getattr(getattr(user, 'branch', None), 'location', None).pk if getattr(getattr(user, 'branch', None), 'location', None) else None
