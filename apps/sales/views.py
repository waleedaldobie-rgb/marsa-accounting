from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from apps.accounts.permissions import require_permission
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.db.models import Q
from decimal import Decimal
from .models import Sale, Shift
from .services import issue_sale, create_sale_draft
from apps.branches.models import Location
from apps.catalog.models import Product

@login_required
@require_permission("view_sales")
def sale_list(request):
    sales = Sale.objects.select_related("branch", "shift", "created_by").order_by("-created_at")
    if request.user.branch_id:
        sales = sales.filter(branch_id=request.user.branch_id)
    q=request.GET.get("q", "").strip()
    status=request.GET.get("status", "").strip()
    channel=request.GET.get("channel", "").strip()
    if q:
        sales=sales.filter(Q(invoice_no__icontains=q) | Q(branch__name__icontains=q))
    if status: sales=sales.filter(status=status)
    if channel: sales=sales.filter(channel=channel)
    page=Paginator(sales, 20).get_page(request.GET.get("page"))
    return render(request, "sales/sales.html", {"sales": page, "page_obj": page, "q":q, "status":status, "channel":channel, "status_choices":Sale.Status.choices, "channel_choices":Sale.Channel.choices})

@login_required
@require_permission("manage_sales")
def pos(request):
    shifts = Shift.objects.filter(
        cashier=request.user, status=Shift.Status.OPEN
    ).select_related("branch").order_by("-opened_at")
    products = Product.objects.filter(is_active=True).prefetch_related("prices")
    if request.method == "POST":
        try:
            shift = get_object_or_404(shifts, pk=request.POST.get("shift_id"))
            product_ids = request.POST.getlist("product_id")
            raw_weights = request.POST.getlist("raw_weight")
            cleaned_weights = request.POST.getlist("cleaned_weight")
            unit_prices = request.POST.getlist("unit_price")
            if not (len(product_ids) == len(raw_weights) == len(cleaned_weights) == len(unit_prices)):
                raise ValidationError("بيانات أصناف الفاتورة غير مكتملة.")
            items = []
            product_map = Product.objects.filter(
                pk__in=product_ids, is_active=True
            ).in_bulk()
            for product_id, raw, cleaned, price in zip(
                product_ids, raw_weights, cleaned_weights, unit_prices
            ):
                product = product_map.get(int(product_id))
                if product is None:
                    raise ValidationError("المنتج المحدد غير صالح.")
                items.append({
                    "product": product,
                    "raw_weight": Decimal(raw),
                    "cleaned_weight": Decimal(cleaned),
                    "unit_price": Decimal(price),
                })
            sale = create_sale_draft(
                user=request.user, shift=shift, branch=shift.branch, items=items
            )
        except (TypeError, ValueError, ArithmeticError, ValidationError) as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "تم إنشاء مسودة الفاتورة.")
            return redirect("sales:detail", pk=sale.pk)
    return render(request, "sales/pos.html", {"shifts": shifts, "products": products})

@login_required
@require_permission("view_sales")
def sale_detail(request, pk):
    sale = get_object_or_404(Sale.objects.prefetch_related("items", "items__processing"), pk=pk)
    if request.user.branch_id and sale.branch_id != request.user.branch_id:
        raise PermissionDenied
    return render(request, "sales/sale_detail.html", {"sale": sale})

@login_required
@require_permission("manage_sales")
def sale_issue(request, pk):
    if request.method != "POST":
        return redirect("sales:detail", pk=pk)
    sale = get_object_or_404(Sale, pk=pk)
    if request.user.branch_id and sale.branch_id != request.user.branch_id:
        raise PermissionDenied
    location_id = request.POST.get("location_id")
    location = get_object_or_404(Location, pk=location_id)
    payment_method = request.POST.get("payment_method", "CASH")
    try:
        issue_sale(sale=sale, location=location, user=request.user, payment_method=payment_method)
    except (ValidationError, ValueError) as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "تم إصدار الفاتورة وخصم الوزن الخام من المخزون.")
    return redirect("sales:detail", pk=pk)

@login_required
@require_permission("view_own_shift")
def shift_list(request):
    shifts = Shift.objects.select_related("cashier", "branch").order_by("-opened_at")
    if request.user.branch_id:
        shifts = shifts.filter(branch_id=request.user.branch_id)
    return render(request, "sales/shifts.html", {"shifts": shifts})

@login_required
@require_permission("open_shift")
def shift_open(request):
    if request.method == "POST":
        if Shift.objects.filter(cashier=request.user, status=Shift.Status.OPEN).exists():
            messages.error(request, "لديك وردية مفتوحة بالفعل.")
            return redirect("sales:shifts")
        branch_id = request.user.branch_id or request.POST.get("branch_id")
        if not branch_id:
            messages.error(request, "يجب تحديد الفرع.")
            return redirect("sales:shifts")
        Shift.objects.create(branch_id=branch_id, cashier=request.user, opening_cash=request.POST.get("opening_cash") or 0)
        messages.success(request, "تم فتح الوردية.")
        return redirect("sales:shifts")
    return render(request, "sales/shift_open.html")
