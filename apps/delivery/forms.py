from django import forms
from .models import Platform

class DeliveryForm(forms.Form):
    platform = forms.ModelChoiceField(queryset=Platform.objects.all())
    external_order_no = forms.CharField(max_length=100)

class SettlementForm(forms.Form):
    amount = forms.DecimalField(max_digits=16, decimal_places=2, min_value=0.01)
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}))
