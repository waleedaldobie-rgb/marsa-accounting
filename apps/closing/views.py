from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import branch_queryset, require_permission
from apps.sales.models import Shift
from .forms import ShiftClosingForm
from .models import ShiftClosing
from .services import create_closing, approve_closing, reject_closing, expected_cash_for_shift

@login_required
@require_permission('manage_closing')
def closing_list(request):
    closings = branch_queryset(ShiftClosing.objects.select_related('shift','shift__cashier','shift__branch','approved_by').order_by('-created_at'), request.user, branch_field='shift__branch')
    return render(request, 'closing/list.html', {'closings': closings})

@login_required
@require_permission('manage_closing')
def closing_create(request, shift_id):
    shift = get_object_or_404(Shift.objects.select_related('branch','cashier'), pk=shift_id)
    if request.user.branch_id and shift.branch_id != request.user.branch_id:
        raise PermissionDenied
    if request.method == 'POST':
        form = ShiftClosingForm(request.POST)
        if form.is_valid():
            try:
                closing = create_closing(shift=shift, actual_cash=form.cleaned_data['actual_cash'], user=request.user)
                messages.success(request, 'تم حفظ مسودة الإغلاق. لم تُغلق الوردية حتى الاعتماد.')
                return redirect('closing:detail', pk=closing.pk)
            except ValidationError as exc:
                form.add_error(None, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    else:
        form = ShiftClosingForm(initial={'actual_cash': expected_cash_for_shift(shift)})
    return render(request, 'closing/form.html', {'form': form, 'shift': shift})

@login_required
@require_permission('manage_closing')
def closing_detail(request, pk):
    closing = get_object_or_404(branch_queryset(ShiftClosing.objects.select_related('shift','shift__cashier','shift__branch','approved_by'), request.user, branch_field='shift__branch'), pk=pk)
    return render(request, 'closing/detail.html', {'closing': closing})

@login_required
@require_permission('approve_closing')
def closing_approve(request, pk):
    closing = get_object_or_404(branch_queryset(ShiftClosing.objects.all(), request.user, branch_field='shift__branch'), pk=pk)
    if request.method == 'POST':
        try:
            approve_closing(closing=closing, user=request.user)
            messages.success(request, 'تم اعتماد الإغلاق وإغلاق الوردية.')
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('closing:detail', pk=pk)

@login_required
@require_permission('approve_closing')
def closing_reject(request, pk):
    closing = get_object_or_404(branch_queryset(ShiftClosing.objects.all(), request.user, branch_field='shift__branch'), pk=pk)
    if request.method == 'POST':
        try:
            reject_closing(closing=closing, user=request.user)
            messages.success(request, 'تم رفض مسودة الإغلاق.')
        except ValidationError as exc:
            messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('closing:detail', pk=pk)
