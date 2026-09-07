from django import forms
from .models import SalesReturn, SalesReturnItem

class SalesReturnForm(forms.ModelForm):
    class Meta:
        model=SalesReturn
        fields=['branch','reason','payment_method']
        widgets={'reason':forms.Textarea(attrs={'rows':3})}

class SalesReturnItemForm(forms.ModelForm):
    class Meta:
        model=SalesReturnItem
        fields=['sale_item','raw_weight']
