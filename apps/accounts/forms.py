from django import forms

from apps.branches.models import Branch
from .models import User


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput, min_length=8, label='كلمة المرور')
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='تأكيد كلمة المرور')

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'role', 'branch', 'is_active')

    def clean(self):
        data = super().clean()
        if data.get('password') != data.get('password_confirm'):
            raise forms.ValidationError('كلمتا المرور غير متطابقتين.')
        if data.get('role') == User.Role.OWNER and not self.user.is_superuser:
            raise forms.ValidationError('لا يمكن إنشاء مالك من هذا الحساب.')
        return data

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'role', 'branch', 'is_active')

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        if user and not user.is_superuser:
            self.fields['role'].choices = [(value, label) for value, label in self.fields['role'].choices if value != User.Role.OWNER]

    def clean(self):
        data = super().clean()
        if self.instance.pk == self.user.pk and data.get('role') and data['role'] != self.instance.role:
            raise forms.ValidationError('لا يمكن تغيير دور المستخدم الحالي من هذه الصفحة.')
        if self.instance.role == User.Role.OWNER and data.get('is_active') is False:
            if User.objects.filter(role=User.Role.OWNER, is_active=True).count() <= 1:
                raise forms.ValidationError('لا يمكن تعطيل آخر مالك نشط.')
        if data.get('role') == User.Role.OWNER and not self.user.is_superuser:
            raise forms.ValidationError('لا يمكن رفع المستخدم إلى مالك.')
        return data
