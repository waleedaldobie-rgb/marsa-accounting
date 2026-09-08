from django import forms
from .models import Expense
from apps.sales.models import Shift


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['branch', 'shift', 'category', 'amount', 'payment_method', 'attachment']
        widgets = {
            'shift': forms.Select(),
            'category': forms.TextInput(attrs={'placeholder': 'مثال: كهرباء، نقل، صيانة'}),
            'amount': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['shift'].queryset = Shift.objects.none()
        if user and user.is_authenticated:
            shifts = Shift.objects.filter(status=Shift.Status.OPEN).select_related('branch').order_by('-opened_at')
            if not user.is_superuser and user.branch_id:
                self.fields['branch'].queryset = self.fields['branch'].queryset.filter(pk=user.branch_id)
                self.fields['branch'].initial = user.branch_id
                shifts = shifts.filter(branch_id=user.branch_id)
            self.fields['shift'].queryset = shifts
        self.fields['shift'].required = False
        self.fields['shift'].empty_label = 'بدون وردية (مصروف غير نقدي/خارجي)'

    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if not attachment:
            return attachment
        allowed = {'.pdf', '.jpg', '.jpeg', '.png'}
        name = attachment.name.lower()
        if not any(name.endswith(ext) for ext in allowed):
            raise forms.ValidationError('نوع الملف غير مسموح. المسموح: PDF أو JPG أو PNG.')
        if attachment.size > 5 * 1024 * 1024:
            raise forms.ValidationError('حجم الملف يجب ألا يتجاوز 5 ميجابايت.')
        return attachment
