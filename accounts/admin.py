from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class MarsaUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (("بيانات مرسى", {"fields": ("role", "branch")}),)
    list_display = ("username", "email", "role", "branch", "is_active")
    list_filter = ("role", "branch", "is_active")
