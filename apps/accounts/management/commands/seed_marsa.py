from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import User
from apps.branches.models import Branch, Location


class Command(BaseCommand):
    help = "Create the initial branches, central warehouse, and optional demo users."

    @transaction.atomic
    def handle(self, *args, **options):
        branches = []
        for code, name in (("BR01", "فرع 1"), ("BR02", "فرع 2")):
            branch, _ = Branch.objects.get_or_create(code=code, defaults={"name": name})
            branches.append(branch)
            Location.objects.get_or_create(
                branch=branch,
                defaults={"name": f"مخزون {name}", "kind": Location.Kind.BRANCH},
            )

        Location.objects.get_or_create(
            kind=Location.Kind.CENTRAL_WAREHOUSE,
            branch=None,
            defaults={"name": "المستودع المركزي"},
        )

        self.stdout.write(self.style.SUCCESS("تم تجهيز فرعين ومستودع مركزي."))
        self.stdout.write("لا يتم إنشاء كلمات مرور افتراضية أو مستخدمين تجريبيين تلقائيًا.")
