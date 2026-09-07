from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import branch_queryset, require_permission
from apps.sales.models import Sale
from .forms import DeliveryForm, SettlementForm
from .models import DeliveryOrder
from .services import create_delivery_order, settle_delivery, update_delivery_status

@login_required
@require_permission('view_delivery')
def delivery_list(request):
    orders = DeliveryOrder.objects.select_related('sale','sale__branch','platform').order_by('-pk')
    if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'OWNER'):
        orders = orders.filter(sale__branch_id=request.user.branch_id)
    return render(request, 'delivery/list.html', {'orders': orders[:300]})

@login_required
@require_permission('view_delivery')
def delivery_detail(request, pk):
    order = get_object_or_404(DeliveryOrder.objects.select_related('sale','sale__branch','platform'), pk=pk)
    if not (request.user.is_superuser or getattr(request.user, 'role', None) == 'OWNER') and order.sale.branch_id != request.user.branch_id:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    return render(request, 'delivery/detail.html', {'order': order, 'settlements': order.settlements.order_by('-settled_at')})

@login_required
@require_permission('view_delivery')
def delivery_create(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related('branch'), pk=sale_id)
    if request.method == 'POST':
        form = DeliveryForm(request.POST)
        if form.is_valid():
            try:
                order = create_delivery_order(sale=sale, platform=form.cleaned_data['platform'], external_order_no=form.cleaned_data['external_order_no'], user=request.user)
                messages.success(request, 'تم إنشاء طلب التوصيل.')
                return redirect('delivery:detail', pk=order.pk)
            except ValidationError as exc:
                form.add_error(None, str(exc))
    else:
        form = DeliveryForm()
    return render(request, 'delivery/form.html', {'form': form, 'sale': sale})

@login_required
@require_permission('view_delivery')
def delivery_status(request, pk, status):
    order = get_object_or_404(DeliveryOrder, pk=pk)
    try:
        update_delivery_status(order=order, status=status, user=request.user, reason=request.POST.get('reason',''))
        messages.success(request, 'تم تحديث حالة التوصيل.')
    except ValidationError as exc:
        messages.error(request, str(exc))
    return redirect('delivery:detail', pk=pk)

@login_required
@require_permission('view_delivery')
def delivery_settle(request, pk):
    order = get_object_or_404(DeliveryOrder, pk=pk)
    form = SettlementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        try:
            settle_delivery(order=order, amount=form.cleaned_data['amount'], user=request.user, note=form.cleaned_data['note'])
            messages.success(request, 'تم تسجيل التسوية وإضافتها إلى الدفتر المالي.')
            return redirect('delivery:detail', pk=pk)
        except ValidationError as exc:
            form.add_error(None, str(exc))
    return render(request, 'delivery/settle.html', {'form': form, 'order': order})
