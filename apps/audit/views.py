from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, render

from apps.accounts.permissions import branch_queryset
from .models import AuditLog


@login_required
def audit_list(request):
    if not (request.user.is_superuser or request.user.is_owner or request.user.role == 'ACCOUNTANT'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    logs = AuditLog.objects.select_related('user', 'branch').order_by('-created_at')
    if not (request.user.is_superuser or request.user.is_owner):
        logs = logs.filter(branch_id=request.user.branch_id)
    for field in ('user_id', 'branch_id', 'action', 'entity'):
        value = request.GET.get(field)
        if value:
            logs = logs.filter(**{field: value})
    if request.GET.get('date_from'):
        logs = logs.filter(created_at__date__gte=request.GET['date_from'])
    if request.GET.get('date_to'):
        logs = logs.filter(created_at__date__lte=request.GET['date_to'])
    page = Paginator(logs, 50).get_page(request.GET.get('page'))
    return render(request, 'audit/list.html', {'page': page, 'logs': page.object_list})


@login_required
def audit_detail(request, pk):
    if not (request.user.is_superuser or request.user.is_owner or request.user.role == 'ACCOUNTANT'):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    logs = AuditLog.objects.select_related('user', 'branch')
    if not (request.user.is_superuser or request.user.is_owner):
        logs = logs.filter(branch_id=request.user.branch_id)
    log = get_object_or_404(logs, pk=pk)
    return render(request, 'audit/detail.html', {'log': log})
