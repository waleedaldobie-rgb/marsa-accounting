from django import forms


class ShiftClosingForm(forms.Form):
    actual_cash = forms.DecimalField(min_value=0, max_digits=16, decimal_places=2, label='النقد الفعلي')
