from django import forms
from .models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem
from apps.catalog.models import Supplier, Product

class PurchaseForm(forms.ModelForm):
    class Meta:
        model=Purchase
        fields=['supplier','location','invoice_no']

class PurchaseItemForm(forms.ModelForm):
    class Meta:
        model=PurchaseItem
        fields=['product','quantity','unit_cost']

class PurchaseReturnForm(forms.ModelForm):
    class Meta:
        model=PurchaseReturn
        fields=['purchase','location','reference_no','reason']

class PurchaseReturnItemForm(forms.ModelForm):
    class Meta:
        model=PurchaseReturnItem
        fields=['product','quantity','unit_cost']
