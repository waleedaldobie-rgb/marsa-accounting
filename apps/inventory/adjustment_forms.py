from django import forms

from apps.branches.models import Branch, Location
from apps.catalog.models import Product


class StockAdjustmentForm(forms.Form):
    location = forms.ModelChoiceField(queryset=Location.objects.filter(kind=Location.Kind.BRANCH, is_active=True), label='موقع الفرع')
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_active=True), label='المنتج')
    counted_quantity = forms.DecimalField(max_digits=14, decimal_places=3, min_value=0, label='الكمية المعدودة')
    reason = forms.CharField(min_length=3, widget=forms.Textarea(attrs={'rows': 3}), label='سبب التسوية')
    item_reason = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 2}), label='ملاحظات الصنف')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not (user.is_superuser or user.is_owner):
            self.fields['location'].queryset = self.fields['location'].queryset.filter(branch_id=user.branch_id)


class AdjustmentDecisionForm(forms.Form):
    reason = forms.CharField(min_length=3, widget=forms.Textarea(attrs={'rows': 2}), label='سبب القرار')
