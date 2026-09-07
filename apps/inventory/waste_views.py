from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render

from apps.accounts.permissions import has_permission, branch_queryset, require_permission
from .forms import WasteAdjustmentForm
from .models import WasteAdjustment
from .waste_services import approve_waste, cancel_waste


@login_required
@require_permission('manage_waste')
def waste_list(request):
    wastes = branch_queryset(WasteAdjustment.objects.select_related('branch', 'location', 'product', 'created_by'), request.user)
    return render(request, 'inventory/waste_list.html', {'wastes': wastes})


@login_required
@require_permission('manage_waste')
def waste_create(request):
    if request.method == 'POST':
        form = WasteAdjustmentForm(request.POST, user=request.user)
        if form.is_valid():
            waste = form.save(commit=False)
            waste.created_by = request.user
            if not request.user.is_superuser and request.user.branch_id:
                waste.branch_id = request.user.branch_id
            waste.full_clean()
            waste.save()
            messages.success(request, 'تم إنشاء سجل الهدر كمسودة. لن يتأثر المخزون حتى الاعتماد.')
            return redirect('inventory:waste_detail', pk=waste.pk)
    else:
        form = WasteAdjustmentForm(user=request.user)
    return render(request, 'inventory/waste_form.html', {'form': form})


@login_required
@require_permission('manage_waste')
def waste_detail(request, pk):
    waste = get_object_or_404(branch_queryset(WasteAdjustment.objects.select_related('branch', 'location', 'product', 'processing_record'), request.user), pk=pk)
    return render(request, 'inventory/waste_detail.html', {'waste': waste})


@login_required
@require_permission('manage_waste')
def waste_approve(request, pk):
    if request.method != 'POST':
        return redirect('expenses:detail' if 'expense' in name else 'inventory:waste_detail', pk=pk)
    waste = get_object_or_404(branch_queryset(WasteAdjustment.objects.all(), request.user), pk=pk)
    try:
        approve_waste(waste=waste, user=request.user)
        messages.success(request, 'تم اعتماد الهدر وتسجيل حركة إخراج من المخزون.')
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('inventory:waste_detail', pk=pk)


@login_required
@require_permission('manage_waste')
def waste_cancel(request, pk):
    if request.method != 'POST':
        return redirect('expenses:detail' if 'expense' in name else 'inventory:waste_detail', pk=pk)
    waste = get_object_or_404(branch_queryset(WasteAdjustment.objects.all(), request.user), pk=pk)
    try:
        cancel_waste(waste=waste, user=request.user)
        messages.success(request, 'تم إلغاء مسودة الهدر.')
    except ValidationError as exc:
        messages.error(request, exc.messages[0] if hasattr(exc, 'messages') else str(exc))
    return redirect('inventory:waste_detail', pk=pk)
