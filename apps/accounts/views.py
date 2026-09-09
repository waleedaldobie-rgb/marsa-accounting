from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from apps.audit.services import log_event
from .forms import UserCreateForm, UserUpdateForm
from .models import User
from .permissions import can_manage_users


def _guard(request):
    if not can_manage_users(request.user):
        raise PermissionDenied


@login_required
def user_list(request):
    _guard(request)
    users = User.objects.select_related('branch').order_by('username')
    return render(request, 'accounts/users/list.html', {'users': users})


@login_required
def user_create(request):
    _guard(request)
    if request.method == 'POST':
        form = UserCreateForm(request.POST, user=request.user)
        if form.is_valid():
            user = form.save()
            log_event(user=request.user, branch=user.branch, action='CREATE_USER', entity='User', entity_id=user.pk, new_value={'username': user.username, 'role': user.role})
            messages.success(request, 'تم إنشاء المستخدم بنجاح.')
            return redirect('accounts:user_detail', pk=user.pk)
    else:
        form = UserCreateForm(user=request.user)
    return render(request, 'accounts/users/form.html', {'form': form, 'title': 'إنشاء مستخدم'})


@login_required
def user_detail(request, pk):
    _guard(request)
    user = get_object_or_404(User.objects.select_related('branch'), pk=pk)
    logs = user.auditlog_set.order_by('-created_at')[:50] if hasattr(user, 'auditlog_set') else []
    return render(request, 'accounts/users/detail.html', {'managed_user': user, 'logs': logs})


@login_required
def user_edit(request, pk):
    _guard(request)
    user = get_object_or_404(User, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, instance=user, user=request.user)
        if form.is_valid():
            updated = form.save()
            log_event(user=request.user, branch=updated.branch, action='UPDATE_USER', entity='User', entity_id=updated.pk, new_value={'username': updated.username, 'role': updated.role, 'is_active': updated.is_active})
            messages.success(request, 'تم تحديث بيانات المستخدم.')
            return redirect('accounts:user_detail', pk=updated.pk)
    else:
        form = UserUpdateForm(instance=user, user=request.user)
    return render(request, 'accounts/users/form.html', {'form': form, 'title': 'تعديل المستخدم', 'managed_user': user})
