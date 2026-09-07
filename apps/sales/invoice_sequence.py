from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import InvoiceSequence


def allocate_invoice_number(*, branch):
    """Allocate a monotonic branch-scoped invoice number under a row lock."""
    with transaction.atomic():
        try:
            with transaction.atomic():
                InvoiceSequence.objects.create(branch=branch, next_number=1)
        except IntegrityError:
            pass
        sequence = InvoiceSequence.objects.select_for_update().get(branch=branch)
        number = sequence.next_number
        sequence.next_number = number + 1
        sequence.save(update_fields=["next_number", "updated_at"])
        return f"{branch.code}-{timezone.localdate():%Y%m%d}-{number:06d}"
