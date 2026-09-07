from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "OWNER", "مالك / مدير النظام"
        ACCOUNTANT = "ACCOUNTANT", "محاسب"
        BRANCH_MANAGER = "BRANCH_MANAGER", "مدير فرع"
        CASHIER = "CASHIER", "كاشير"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.CASHIER)
    branch = models.ForeignKey(
        "branches.Branch", null=True, blank=True, on_delete=models.SET_NULL, related_name="users"
    )

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def is_owner(self):
        return self.is_superuser or self.role == self.Role.OWNER

    @property
    def can_approve(self):
        return self.is_owner or self.role == self.Role.ACCOUNTANT
