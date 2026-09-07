from django import forms
from django.utils import timezone
from .models import Product, ProductPrice, Supplier


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ["name", "sku", "description", "is_active"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "مثال: هامور"}),
            "sku": forms.TextInput(attrs={"placeholder": "HAM-001", "dir": "ltr"}),
            "description": forms.Textarea(attrs={"rows": 3}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ["name", "phone", "notes", "is_active"]
        widgets = {"notes": forms.Textarea(attrs={"rows": 3})}


class ProductPriceForm(forms.ModelForm):
    class Meta:
        model = ProductPrice
        fields = ["price", "starts_at", "ends_at"]
        widgets = {
            "starts_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
            "ends_at": forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("starts_at", "ends_at"):
            self.fields[name].input_formats = ["%Y-%m-%dT%H:%M"]
        if not self.instance.pk and not self.initial.get("starts_at"):
            self.initial["starts_at"] = timezone.localtime().strftime("%Y-%m-%dT%H:%M")
