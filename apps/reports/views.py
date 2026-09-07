from datetime import datetime, time
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.db.models import Count, F, Sum, Value, DecimalField, ExpressionWrapper
from django.db.models.functions import Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.accounts.permissions import branch_queryset, require_permission
from apps.expenses.models import Expense
from apps.inventory.models import StockBalance, StockMovement, WasteAdjustment
from apps.sales.models import PaymentTransaction, Sale, SaleItem, Shift

ZERO = Decimal("0")


def _date_range(request):
    """Return an inclusive aware datetime range from optional YYYY-MM-DD GET params."""
    today = timezone.localdate()
    try:
        start_date = datetime.strptime(request.GET.get("date_from", ""), "%Y-%m-%d").date()
    except ValueError:
        start_date = today
    try:
        end_date = datetime.strptime(request.GET.get("date_to", ""), "%Y-%m-%d").date()
    except ValueError:
        end_date = today
    if start_date > end_date:
        start_date, end_date = end_date, start_date
    start = timezone.make_aware(datetime.combine(start_date, time.min))
    end = timezone.make_aware(datetime.combine(end_date, time.max))
    return start, end, start_date, end_date


def _filter_period(qs, field, start, end):
    return qs.filter(**{f"{field}__gte": start, f"{field}__lte": end})


@login_required
@require_permission("view_reports")
def dashboard(request):
    start, end, date_from, date_to = _date_range(request)

    sales = _filter_period(
        branch_queryset(Sale.objects.filter(status=Sale.Status.ISSUED), request.user),
        "issued_at", start, end,
    )
    expenses = _filter_period(
        branch_queryset(Expense.objects.filter(status=Expense.Status.APPROVED), request.user),
        "created_at", start, end,
    )
    shifts = branch_queryset(Shift.objects.all(), request.user)
    sales_items = _filter_period(
        SaleItem.objects.filter(sale__status=Sale.Status.ISSUED), "sale__issued_at", start, end
    )
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "OWNER"):
        sales_items = sales_items.filter(sale__branch_id=request.user.branch_id)

    sales_total = sales.aggregate(v=Sum("total"))["v"] or ZERO
    expense_total = expenses.aggregate(v=Sum("amount"))["v"] or ZERO
    cogs_total = sales_items.aggregate(v=Sum("cogs"))["v"] or ZERO
    gross_profit = sales_total - cogs_total
    net_profit = gross_profit - expense_total

    payment_in = _filter_period(
        branch_queryset(PaymentTransaction.objects.filter(direction=PaymentTransaction.Direction.IN), request.user),
        "created_at", start, end,
    ).aggregate(v=Sum("amount"))["v"] or ZERO
    payment_out = _filter_period(
        branch_queryset(PaymentTransaction.objects.filter(direction=PaymentTransaction.Direction.OUT), request.user),
        "created_at", start, end,
    ).aggregate(v=Sum("amount"))["v"] or ZERO

    top_products = sales_items.values("product__name", "product__sku").annotate(
        quantity=Sum("raw_weight"), revenue=Sum("sale_amount"), cogs=Sum("cogs")
    ).annotate(
        profit=ExpressionWrapper(F("revenue") - F("cogs"), output_field=DecimalField(max_digits=18, decimal_places=4))
    ).order_by("-revenue")[:10]

    return render(request, "reports/dashboard.html", {
        "date_from": date_from, "date_to": date_to,
        "sales_total": sales_total, "expense_total": expense_total,
        "cogs_total": cogs_total, "gross_profit": gross_profit, "net_profit": net_profit,
        "payment_in": payment_in, "payment_out": payment_out,
        "open_shifts": shifts.filter(status=Shift.Status.OPEN).count(),
        "invoice_count": sales.count(), "top_products": top_products,
    })


@login_required
@require_permission("view_reports")
def sales_report(request):
    start, end, date_from, date_to = _date_range(request)
    sales = _filter_period(
        branch_queryset(Sale.objects.filter(status=Sale.Status.ISSUED).select_related("branch", "shift__cashier"), request.user),
        "issued_at", start, end,
    ).order_by("-issued_at")
    items = SaleItem.objects.filter(sale__in=sales).select_related("product")
    summary = items.aggregate(
        raw=Sum("raw_weight"), cleaned=Sum("cleaned_weight"), revenue=Sum("sale_amount"), cogs=Sum("cogs")
    )
    summary = {k: (v or ZERO) for k, v in summary.items()}
    summary["profit"] = summary["revenue"] - summary["cogs"]
    return render(request, "reports/sales.html", {
        "sales": sales[:300], "summary": summary, "date_from": date_from, "date_to": date_to,
    })


@login_required
@require_permission("view_reports")
def inventory_report(request):
    balances = StockBalance.objects.select_related("product", "location", "location__branch")
    if not (request.user.is_superuser or getattr(request.user, "role", None) == "OWNER"):
        balances = balances.filter(location__branch_id=request.user.branch_id)
    balances = balances.filter(quantity__gt=0).annotate(
        stock_value=ExpressionWrapper(F("quantity") * F("average_cost"), output_field=DecimalField(max_digits=20, decimal_places=4))
    ).order_by("location__name", "product__name")
    totals = balances.aggregate(quantity=Sum("quantity"), value=Sum("stock_value"))
    return render(request, "reports/inventory.html", {
        "balances": balances, "total_quantity": totals["quantity"] or ZERO,
        "total_value": totals["value"] or ZERO,
    })


@login_required
@require_permission("view_reports")
def waste_report(request):
    start, end, date_from, date_to = _date_range(request)
    wastes = _filter_period(
        branch_queryset(WasteAdjustment.objects.filter(status=WasteAdjustment.Status.APPROVED).select_related("branch", "product"), request.user),
        "approved_at", start, end,
    ).order_by("-approved_at")
    movement_ids = StockMovement.objects.filter(
        movement_type=StockMovement.Type.WASTE_OUT,
        reference_type="WasteAdjustment",
        reference_id__in=[str(pk) for pk in wastes.values_list("pk", flat=True)],
    ).values_list("pk", flat=True)
    total_quantity = wastes.aggregate(v=Sum("quantity"))["v"] or ZERO
    total_cost = StockMovement.objects.filter(pk__in=movement_ids).aggregate(v=Sum("total_cost"))["v"] or ZERO
    by_type = wastes.values("waste_type").annotate(quantity=Sum("quantity")).order_by("-quantity")
    return render(request, "reports/waste.html", {
        "wastes": wastes[:300], "by_type": by_type, "total_quantity": total_quantity,
        "total_cost": total_cost, "date_from": date_from, "date_to": date_to,
    })


@login_required
@require_permission("view_reports")
def financial_ledger(request):
    start, end, date_from, date_to = _date_range(request)
    txns = _filter_period(
        branch_queryset(PaymentTransaction.objects.select_related("branch", "shift", "created_by").order_by("-created_at"), request.user),
        "created_at", start, end,
    )
    total_in = txns.filter(direction=PaymentTransaction.Direction.IN).aggregate(v=Sum("amount"))["v"] or ZERO
    total_out = txns.filter(direction=PaymentTransaction.Direction.OUT).aggregate(v=Sum("amount"))["v"] or ZERO
    return render(request, "reports/ledger.html", {
        "transactions": txns[:300], "total_in": total_in, "total_out": total_out,
        "net": total_in - total_out, "date_from": date_from, "date_to": date_to,
    })


@login_required
@require_permission("view_reports")
def export_sales_csv(request):
    start, end, _, _ = _date_range(request)
    sales = _filter_period(
        branch_queryset(Sale.objects.filter(status=Sale.Status.ISSUED).select_related("branch"), request.user),
        "issued_at", start, end,
    ).order_by("issued_at")
    response = HttpResponse(content_type="text/csv; charset=utf-8-sig")
    response["Content-Disposition"] = 'attachment; filename="marsa-sales.csv"'
    response.write("sep=,\n"
                   "الفاتورة,الفرع,التاريخ,الإجمالي,الحالة\n")
    for sale in sales:
        response.write(f"{sale.invoice_no},{sale.branch.name},{sale.issued_at:%Y-%m-%d %H:%M},{sale.total},{sale.get_status_display()}\n")
    return response


def health(request):
    return JsonResponse({"status": "ok", "service": "marsa"})
