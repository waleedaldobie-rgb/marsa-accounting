from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Q


ROLE_PERMISSIONS = {
    "OWNER": {"*"},
    "ACCOUNTANT": {
        "view_reports", "manage_purchases", "approve_purchases", "manage_expenses", "manage_waste",
        "approve_expenses", "manage_closing", "approve_closing", "manage_adjustments",
        "view_inventory", "view_sales", "view_delivery", "view_catalog", "manage_catalog",
    },
    "BRANCH_MANAGER": {
        "view_inventory", "receive_transfers", "create_transfers", "manage_sales",
        "manage_waste", "view_reports", "view_catalog", "view_purchases", "view_delivery",
    },
    "CASHIER": {
        "open_shift", "manage_sales", "view_sales", "view_catalog", "view_own_shift",
    },
}


def has_role(user, *roles):
    return bool(user and user.is_authenticated and (user.is_superuser or user.role in roles))


def has_permission(user, permission):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser or "*" in ROLE_PERMISSIONS.get(user.role, set()):
        return True
    return permission in ROLE_PERMISSIONS.get(user.role, set())


def require_permission(permission):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not has_permission(request.user, permission):
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator


def branch_queryset(queryset, user, branch_field="branch"):
    """Server-side branch scope. Owners can see all; other users see their branch."""
    if has_role(user, "OWNER") or getattr(user, "is_superuser", False):
        return queryset
    branch_id = getattr(user, "branch_id", None)
    if not branch_id:
        return queryset.none()
    return queryset.filter(**{f"{branch_field}_id": branch_id})


def require_same_branch(user, branch_id):
    if has_role(user, "OWNER") or getattr(user, "is_superuser", False):
        return True
    return bool(user.branch_id and int(user.branch_id) == int(branch_id))


def can_create_sale(user, branch_id, shift=None):
    if not has_permission(user, "manage_sales") or not require_same_branch(user, branch_id):
        return False
    return bool(shift is None or user.is_superuser or shift.cashier_id == user.pk)


def can_open_shift(user, branch_id):
    return has_permission(user, "open_shift") and require_same_branch(user, branch_id)


def can_return_sale(user, sale):
    return has_permission(user, "manage_sales") and require_same_branch(user, sale.branch_id)


def can_manage_expense(user, branch_id):
    return has_permission(user, "manage_expenses") and require_same_branch(user, branch_id)


def can_approve_expense(user, expense):
    return has_permission(user, "approve_expenses") and require_same_branch(user, expense.branch_id)


def can_manage_waste(user, branch_id):
    return has_permission(user, "manage_waste") and require_same_branch(user, branch_id)


def can_approve_waste(user, waste):
    return has_permission(user, "manage_waste") and require_same_branch(user, waste.branch_id)


def can_view_inventory(user):
    return has_permission(user, "view_inventory")


def can_view_audit(user):
    return has_role(user, "OWNER", "ACCOUNTANT")


def can_issue_sale(user, sale):
    return has_permission(user, "manage_sales") and require_same_branch(user, sale.branch_id)


def can_approve_purchase(user, purchase):
    if not has_permission(user, "approve_purchases"):
        return False
    if purchase.location.branch_id is None:
        return has_role(user, "OWNER", "ACCOUNTANT")
    return require_same_branch(user, purchase.location.branch_id)


def branch_or_central_queryset(queryset, user, branch_field="branch"):
    """Scope branch documents while allowing accountant/owner access to central records."""
    if has_role(user, "OWNER") or getattr(user, "is_superuser", False):
        return queryset
    branch_id = getattr(user, "branch_id", None)
    if not branch_id:
        return queryset.none()
    if has_role(user, "ACCOUNTANT"):
        return queryset.filter(Q(**{f"{branch_field}_id": branch_id}) | Q(**{f"{branch_field}_id__isnull": True}))
    return queryset.filter(**{f"{branch_field}_id": branch_id})


def can_create_transfer(user, source):
    return has_permission(user, "create_transfers") and require_same_branch(user, source.branch_id)


def can_receive_transfer(user, destination):
    return has_permission(user, "receive_transfers") and require_same_branch(user, destination.branch_id)


def can_close_shift(user, shift):
    if not require_same_branch(user, shift.branch_id):
        return False
    return bool(
        has_permission(user, "manage_closing")
        or (has_permission(user, "view_own_shift") and shift.cashier_id == user.pk)
    )


def can_view_reports(user):
    return has_permission(user, "view_reports")
