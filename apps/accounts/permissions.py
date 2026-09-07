from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404


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
        "open_shift", "manage_sales", "view_catalog", "view_own_shift",
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
