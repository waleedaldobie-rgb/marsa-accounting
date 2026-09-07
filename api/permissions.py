from rest_framework.permissions import BasePermission

from apps.accounts.permissions import has_permission, has_role


class MarsaPermission(BasePermission):
    required_permission = None
    allowed_roles = ()

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if self.required_permission and has_permission(request.user, self.required_permission):
            return True
        return bool(self.allowed_roles and has_role(request.user, *self.allowed_roles))


class IsOwnerOrAccountant(MarsaPermission):
    allowed_roles = ("OWNER", "ACCOUNTANT")


class IsOwnerAccountantOrManager(MarsaPermission):
    allowed_roles = ("OWNER", "ACCOUNTANT", "BRANCH_MANAGER")


def in_user_branch(user, branch_id):
    return user.is_superuser or user.is_owner or bool(user.branch_id and int(user.branch_id) == int(branch_id))


def scoped_queryset(queryset, user, branch_field="branch"):
    if user.is_superuser or user.is_owner:
        return queryset
    branch_id = getattr(user, "branch_id", None)
    if not branch_id:
        return queryset.none()
    return queryset.filter(**{f"{branch_field}_id": branch_id})
