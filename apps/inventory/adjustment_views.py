from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import branch_queryset, has_permission, require_permission
from apps.audit.models import AuditLog
from .adjustment_forms import AdjustmentDecisionForm, StockAdjustmentForm
from .adjustment_services import approve_adjustment, cancel_adjustment, create_adjustment
from .models import StockAdjustment, StockMovement


@login_required
@require_permission('manage_adjustments')
def adjustment_list(request):
    adjustments = branch_queryset(StockAdjustment.objects.select_related('branch', 'location', 'created_by', 'approved_by').prefetch_related('items__product'), request.user)
    return render(request, 'inventory/adjustments/list.html', {'adjustments': adjustments})


@login_required
@require_permission('manage_adjustments')
def adjustment_create(request):
    if request.method == 'POST':
        form = StockAdjustmentForm(request.POST, user=request.user)
        if form.is_valid():
            location = form.cleaned_data['location']
            try:
                adjustment = create_adjustment(
                    user=request.user, branch=location.branch, location=location,
                    reason=form.cleaned_data['reason'],
                    items=[{'product': form.cleaned_data['product'], 'counted_quantity': form.cleaned_data['counted_quantity'], 'reason': form.cleaned_data['item_reason']}],
                )
            except (ValidationError, ValueError) as exc:
                form.add_error(None, str(exc))
            else:
                messages.success(request, 'تم حفظ تسوية المخزون كمسودة.')
                return redirect('inventory:adjustment_detail', pk=adjustment.pk)
    else:
        form = StockAdjustmentForm(user=request.user)
    return render(request, 'inventory/adjustments/form.html', {'form': form})


@login_required
@require_permission('manage_adjustments')
def adjustment_detail(request, pk):
    adjustment = get_object_or_404(branch_queryset(StockAdjustment.objects.select_related('branch', 'location', 'created_by', 'approved_by').prefetch_related('items__product'), request.user), pk=pk)
    movements = StockMovement.objects.filter(reference_type='StockAdjustment', reference_id=str(pk)).select_related('product', 'created_by')
    return render(request, 'inventory/adjustments/detail.html', {'adjustment': adjustment, 'movements': movements, 'decision_form': AdjustmentDecisionForm(), 'can_approve': has_permission(request.user, 'approve_adjustments')})


@login_required
@require_permission('approve_adjustments')
def adjustment_approve(request, pk):
    if request.method != 'POST':
        return redirect('inventory:adjustment_detail', pk=pk)
    adjustment = get_object_or_404(branch_queryset(StockAdjustment.objects.all(), request.user), pk=pk)
    try:
        approve_adjustment(adjustment=adjustment, user=request.user)
        messages.success(request, 'تم اعتماد التسوية وإنشاء حركة المخزون.')
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('inventory:adjustment_detail', pk=pk)


@login_required
@require_permission('manage_adjustments')
def adjustment_cancel(request, pk):
    if request.method != 'POST':
        return redirect('inventory:adjustment_detail', pk=pk)
    form = AdjustmentDecisionForm(request.POST)
    if not form.is_valid():
        messages.error(request, 'سبب الإلغاء مطلوب.')
        return redirect('inventory:adjustment_detail', pk=pk)
    adjustment = get_object_or_404(branch_queryset(StockAdjustment.objects.all(), request.user), pk=pk)
    try:
        cancel_adjustment(adjustment=adjustment, user=request.user, reason=form.cleaned_data['reason'])
        messages.success(request, 'تم إلغاء مسودة التسوية.')
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    return redirect('inventory:adjustment_detail', pk=pk)
