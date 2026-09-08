import csv
import io
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from apps.accounts.permissions import has_permission, require_permission
from .forms import ProductForm, ProductPriceForm, SupplierForm
from .models import Product, ProductPrice, Supplier


def _catalog_write_allowed(user):
    return has_permission(user, "manage_catalog")


@login_required
@require_permission("view_catalog")
def product_list(request):
    products = Product.objects.all()
    q = request.GET.get("q", "").strip()
    if q:
        products = products.filter(name__icontains=q) | Product.objects.filter(sku__icontains=q)
    return render(request, "catalog/products.html", {"products": products, "q": q})


@login_required
@require_permission("view_catalog")
def supplier_list(request):
    q = request.GET.get("q", "").strip()
    suppliers = Supplier.objects.all()
    if q:
        suppliers = suppliers.filter(name__icontains=q) | Supplier.objects.filter(phone__icontains=q)
    return render(request, "catalog/suppliers.html", {"suppliers": suppliers, "q": q})


@login_required
@require_permission("view_catalog")
def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, "catalog/product_detail.html", {"product": product, "price_form": ProductPriceForm()})


@login_required
@require_permission("view_catalog")
def product_create(request):
    if not _catalog_write_allowed(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        product = form.save()
        messages.success(request, "تم إنشاء المنتج بنجاح.")
        return redirect("catalog:product_detail", product.pk)
    return render(request, "catalog/product_form.html", {"form": form, "title": "إضافة منتج"})


@login_required
@require_permission("view_catalog")
def supplier_create(request):
    if not _catalog_write_allowed(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    form = SupplierForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "تم إضافة المورد بنجاح.")
        return redirect("catalog:suppliers")
    return render(request, "catalog/supplier_form.html", {"form": form, "title": "إضافة مورد"})


@login_required
@require_permission("view_catalog")
def add_price(request, pk):
    if not _catalog_write_allowed(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    product = get_object_or_404(Product, pk=pk)
    form = ProductPriceForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        price = form.save(commit=False)
        price.product = product
        try:
            price.full_clean()
            price.save()
        except ValidationError as exc:
            form.add_error(None, exc)
        else:
            messages.success(request, "تم إضافة فترة السعر.")
            return redirect("catalog:product_detail", pk)
    return render(request, "catalog/product_detail.html", {"product": product, "price_form": form})


@login_required
@require_permission("view_catalog")
def product_csv_template(request):
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="marsa-products-template.csv"'
    response.write("\ufeff")
    writer = csv.writer(response)
    writer.writerow(["sku", "name", "description", "is_active", "price", "starts_at", "ends_at"])
    writer.writerow(["HAM-001", "هامور", "", "1", "40.00", "2026-09-08T00:00", ""])
    return response


@login_required
@require_permission("view_catalog")
def product_csv_import(request):
    if not _catalog_write_allowed(request.user):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    if request.method != "POST":
        return render(request, "catalog/import.html")
    upload = request.FILES.get("file")
    if not upload:
        messages.error(request, "اختر ملف CSV أولاً.")
        return redirect("catalog:import")
    try:
        text = upload.read().decode("utf-8-sig")
        rows = csv.DictReader(io.StringIO(text))
        required = {"sku", "name"}
        if not required.issubset(set(rows.fieldnames or [])):
            raise ValueError("يجب أن يحتوي الملف على الأعمدة: sku, name")
        created = updated = 0
        with transaction.atomic():
            for row in rows:
                sku = (row.get("sku") or "").strip().upper()
                name = (row.get("name") or "").strip()
                if not sku or not name:
                    raise ValueError("كل صف يجب أن يحتوي sku و name")
                product, was_created = Product.objects.update_or_create(
                    sku=sku,
                    defaults={"name": name, "description": (row.get("description") or "").strip(), "is_active": (row.get("is_active") or "1").strip().lower() not in {"0", "false", "no"}},
                )
                created += int(was_created)
                updated += int(not was_created)
                if (row.get("price") or "").strip():
                    price = ProductPrice(
                        product=product,
                        price=(row["price"] or "0").strip(),
                        starts_at=(row.get("starts_at") or "").strip(),
                        ends_at=(row.get("ends_at") or "").strip() or None,
                    )
                    from django.utils.dateparse import parse_datetime
                    price.starts_at = parse_datetime(price.starts_at)
                    if price.ends_at:
                        price.ends_at = parse_datetime(price.ends_at)
                    price.full_clean()
                    price.save()
    except Exception as exc:
        messages.error(request, f"فشل الاستيراد: {exc}")
    else:
        messages.success(request, f"تم الاستيراد: {created} جديد، {updated} محدث.")
    return redirect("catalog:products")
