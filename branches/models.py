from django.db import models

class Branch(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=120)
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.code} - {self.name}"

class Warehouse(models.Model):
    class WarehouseType(models.TextChoices):
        CENTRAL = "central", "مركزي"
        BRANCH = "branch", "فرعي"

    name = models.CharField(max_length=120)
    warehouse_type = models.CharField(max_length=20, choices=WarehouseType.choices, default=WarehouseType.CENTRAL)
    branch = models.OneToOneField(Branch, null=True, blank=True, on_delete=models.PROTECT, related_name="warehouse")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name
