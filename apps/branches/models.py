from django.core.exceptions import ValidationError
from django.db import models


class Branch(models.Model):
    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=150)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} - {self.name}"


class Location(models.Model):
    class Kind(models.TextChoices):
        CENTRAL_WAREHOUSE = "CENTRAL_WAREHOUSE", "المستودع المركزي"
        BRANCH = "BRANCH", "فرع"

    name = models.CharField(max_length=150)
    kind = models.CharField(max_length=30, choices=Kind.choices)
    branch = models.OneToOneField(
        Branch, null=True, blank=True, on_delete=models.CASCADE, related_name="location"
    )
    is_active = models.BooleanField(default=True)

    def clean(self):
        if self.kind == self.Kind.BRANCH and not self.branch_id:
            raise ValidationError({"branch": "موقع الفرع يجب أن يرتبط بفرع."})
        if self.kind == self.Kind.CENTRAL_WAREHOUSE and self.branch_id:
            raise ValidationError({"branch": "المستودع المركزي لا يرتبط بفرع."})

    def __str__(self):
        return self.name
