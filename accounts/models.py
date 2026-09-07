from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    class Role(models.TextChoices):
        OWNER = "owner", "المالك"
        ACCOUNTANT = "accountant", "المحاسب"
        BRANCH_MANAGER = "branch_manager", "مدير الفرع"
        CASHIER = "cashier", "الكاشير"

    role = models.CharField(max_length=30, choices=Role.choices, default=Role.CASHIER)
    branch = models.ForeignKey("branches.Branch", null=True, blank=True, on_delete=models.PROTECT, related_name="users")

    def __str__(self):
        return self.get_full_name() or self.username
