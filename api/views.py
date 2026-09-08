from decimal import Decimal

from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate, get_user_model
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import has_permission, has_role, branch_or_central_queryset, branch_queryset
from apps.branches.models import Branch, Location
from apps.catalog.models import Product, ProductPrice, Supplier
from apps.closing.models import ShiftClosing
from apps.closing.services import approve_closing, create_closing, expected_cash_for_shift
from apps.expenses.models import Expense
from apps.expenses.services import approve_expense
from apps.inventory.models import StockBalance, StockMovement
from apps.purchases.models import Purchase, PurchaseReturn
from apps.purchases.services import approve_purchase, approve_purchase_return
from apps.reports.views import _date_range, _filter_period
from apps.sales.models import Sale, SalesReturn, Shift
from apps.sales.return_services import approve_sales_return
from apps.sales.services import create_sale_draft, issue_sale
from apps.transfers.models import Transfer
from apps.transfers.services import receive_transfer, send_transfer

from .permissions import in_user_branch, scoped_queryset
from .serializers import (
    BranchSerializer, ExpenseSerializer, LocationSerializer, ProductPriceSerializer,
    ProductSerializer, PurchaseReturnSerializer, PurchaseSerializer, SaleSerializer,
    SalesReturnSerializer, ShiftClosingSerializer, ShiftSerializer, StockBalanceSerializer,
    StockMovementSerializer, SupplierSerializer, TransferSerializer,
)


def forbidden(message="ليس لديك صلاحية تنفيذ هذا الإجراء."):
    return Response({"detail": message}, status=status.HTTP_403_FORBIDDEN)


def bad(exc):
    if isinstance(exc, ValidationError):
        detail = exc.message_dict if hasattr(exc, "message_dict") else exc.messages
    else:
        detail = str(exc)
    return Response({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)


def require(user, permission=None, roles=()):
    return (permission and has_permission(user, permission)) or (roles and has_role(user, *roles))


class TokenLoginView(ObtainAuthToken):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        user = authenticate(request=request, username=request.data.get("username"), password=request.data.get("password"))
        if user is None:
            return Response({"detail": "بيانات الدخول غير صحيحة."}, status=status.HTTP_400_BAD_REQUEST)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": {"id": user.pk, "username": user.username, "role": user.role, "branch": user.branch_id}})


class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({"id": u.pk, "username": u.username, "email": u.email, "role": u.role, "branch": u.branch_id, "is_staff": u.is_staff})


class CatalogView(APIView):
    def get(self, request):
        products = Product.objects.filter(is_active=True).prefetch_related("prices")
        suppliers = Supplier.objects.filter(is_active=True)
        return Response({"products": ProductSerializer(products, many=True).data, "suppliers": SupplierSerializer(suppliers, many=True).data})

    def post(self, request):
        if not require(request.user, "manage_catalog"):
            return forbidden()
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data if serializer.save() else serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    def get(self, request, pk):
        return Response(ProductSerializer(get_object_or_404(Product, pk=pk), context={"request": request}).data)

    def patch(self, request, pk):
        if not require(request.user, "manage_catalog"):
            return forbidden()
        product = get_object_or_404(Product, pk=pk)
        serializer = ProductSerializer(product, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class PriceView(APIView):
    def get(self, request):
        qs = ProductPrice.objects.all().order_by("-starts_at")
        product = request.query_params.get("product")
        if product:
            qs = qs.filter(product_id=product)
        return Response(ProductPriceSerializer(qs, many=True).data)

    def post(self, request):
        if not require(request.user, "manage_catalog"):
            return forbidden()
        serializer = ProductPriceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierView(APIView):
    def get(self, request):
        return Response(SupplierSerializer(Supplier.objects.filter(is_active=True), many=True).data)

    def post(self, request):
        if not require(request.user, "manage_catalog"):
            return forbidden()
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BranchLocationView(APIView):
    def get(self, request):
        branches = Branch.objects.filter(is_active=True)
        locations = Location.objects.filter(is_active=True)
        if not (request.user.is_superuser or request.user.is_owner):
            branches = branches.filter(pk=request.user.branch_id)
            locations = locations.filter(branch_id=request.user.branch_id)
        return Response({"branches": BranchSerializer(branches, many=True).data, "locations": LocationSerializer(locations, many=True).data})


class InventoryView(APIView):
    def get(self, request):
        balances = StockBalance.objects.select_related("product", "location")
        movements = StockMovement.objects.select_related("product", "location", "created_by").order_by("-created_at")
        if not (request.user.is_superuser or request.user.is_owner):
            balances = balances.filter(location__branch_id=request.user.branch_id)
            movements = movements.filter(location__branch_id=request.user.branch_id)
        return Response({"balances": StockBalanceSerializer(balances, many=True).data, "movements": StockMovementSerializer(movements[:500], many=True).data})


class PurchaseView(APIView):
    def get(self, request, pk=None):
        qs = Purchase.objects.select_related("supplier", "location").prefetch_related("items")
        qs = scoped_queryset(qs, request.user, "location__branch") if not (request.user.is_superuser or request.user.is_owner) else qs
        if pk:
            return Response(PurchaseSerializer(get_object_or_404(qs, pk=pk)).data)
        return Response(PurchaseSerializer(qs.order_by("-created_at"), many=True).data)

    def post(self, request):
        if not require(request.user, "manage_purchases"):
            return forbidden()
        serializer = PurchaseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        location = get_object_or_404(Location, pk=serializer.validated_data["location"].pk)
        if not (request.user.is_superuser or request.user.is_owner or (request.user.role == "ACCOUNTANT" and location.branch_id is None) or location.branch_id == request.user.branch_id):
            return forbidden("لا يمكنك إنشاء شراء خارج فرعك.")
        serializer.save(created_by=request.user)
        return Response(PurchaseSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)


class PurchaseApproveView(APIView):
    def post(self, request, pk):
        if not require(request.user, "approve_purchases"):
            return forbidden()
        purchase = get_object_or_404(branch_or_central_queryset(Purchase.objects.select_related("location"), request.user, "location__branch"), pk=pk)
        try:
            return Response(PurchaseSerializer(approve_purchase(purchase_id=pk, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class PurchaseReturnView(APIView):
    def post(self, request, pk=None, action=None):
        if action == "approve":
            return self.approve(request, pk)
        if not require(request.user, "manage_purchases"):
            return forbidden()
        serializer = PurchaseReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not in_user_branch(request.user, serializer.validated_data["location"].branch_id):
            return forbidden()
        serializer.save(created_by=request.user)
        return Response(PurchaseReturnSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def approve(self, request, pk):
        if not require(request.user, "approve_purchases"):
            return forbidden()
        ret = get_object_or_404(branch_or_central_queryset(PurchaseReturn.objects.select_related("location"), request.user, "location__branch"), pk=pk)
        try:
            return Response(PurchaseReturnSerializer(approve_purchase_return(return_obj=ret, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class ShiftView(APIView):
    def get(self, request):
        qs = Shift.objects.select_related("branch", "cashier").order_by("-opened_at")
        if not (request.user.is_superuser or request.user.is_owner):
            qs = qs.filter(branch_id=request.user.branch_id)
        return Response(ShiftSerializer(qs, many=True).data)

    def post(self, request):
        if not require(request.user, "open_shift"):
            return forbidden()
        branch_id = request.data.get("branch") or request.user.branch_id
        if not in_user_branch(request.user, branch_id):
            return forbidden("لا يمكنك فتح وردية خارج فرعك.")
        if Shift.objects.filter(cashier=request.user, status=Shift.Status.OPEN).exists():
            return bad("لديك وردية مفتوحة بالفعل.")
        serializer = ShiftSerializer(data={"branch": branch_id, "opening_cash": request.data.get("opening_cash", 0)})
        serializer.is_valid(raise_exception=True)
        shift = serializer.save(cashier=request.user)
        return Response(ShiftSerializer(shift).data, status=status.HTTP_201_CREATED)


class SaleView(APIView):
    def get(self, request, pk=None):
        qs = Sale.objects.select_related("branch", "shift", "created_by").prefetch_related("items")
        if not (request.user.is_superuser or request.user.is_owner):
            qs = qs.filter(branch_id=request.user.branch_id)
        if pk:
            return Response(SaleSerializer(get_object_or_404(qs, pk=pk)).data)
        return Response(SaleSerializer(qs.order_by("-created_at"), many=True).data)

    def post(self, request):
        if not require(request.user, "manage_sales"):
            return forbidden()
        serializer = SaleSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        shift_qs = Shift.objects.select_related("branch")
        if not (request.user.is_superuser or request.user.is_owner):
            shift_qs = shift_qs.filter(branch_id=request.user.branch_id, cashier=request.user)
        shift = get_object_or_404(shift_qs, pk=serializer.validated_data["shift"].pk)
        items = serializer.validated_data.get("items", [])
        try:
            sale = create_sale_draft(user=request.user, shift=shift, branch=shift.branch, items=items)
            return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class SaleIssueView(APIView):
    def post(self, request, pk):
        if not require(request.user, "manage_sales"):
            return forbidden()
        sale = get_object_or_404(branch_queryset(Sale.objects.select_related("branch"), request.user), pk=pk)
        location = get_object_or_404(Location, pk=request.data.get("location"))
        try:
            sale = issue_sale(sale=sale, location=location, user=request.user, payment_method=request.data.get("payment_method", "CASH"))
            return Response(SaleSerializer(sale).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class SalesReturnView(APIView):
    def post(self, request, pk=None, action=None):
        if action == "approve":
            return self.approve(request, pk)
        if not require(request.user, roles=("OWNER", "ACCOUNTANT", "BRANCH_MANAGER")):
            return forbidden()
        serializer = SalesReturnSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        sale = serializer.validated_data["sale"]
        if not in_user_branch(request.user, sale.branch_id):
            return forbidden()
        serializer.save(created_by=request.user, branch_id=sale.branch_id)
        return Response(SalesReturnSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def approve(self, request, pk):
        if not require(request.user, roles=("OWNER", "ACCOUNTANT", "BRANCH_MANAGER")):
            return forbidden()
        ret = get_object_or_404(branch_queryset(SalesReturn.objects.select_related("branch"), request.user), pk=pk)
        location = get_object_or_404(Location, pk=request.data.get("location"))
        try:
            return Response(SalesReturnSerializer(approve_sales_return(sales_return=ret, location=location, user=request.user, request=request)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class TransferView(APIView):
    def post(self, request, pk=None, action=None):
        if action == "send":
            return self.send(request, pk)
        if action == "receive":
            return self.receive(request, pk)
        if not require(request.user, "create_transfers"):
            return forbidden()
        serializer = TransferSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not in_user_branch(request.user, serializer.validated_data["source"].branch_id):
            return forbidden()
        serializer.save(created_by=request.user)
        return Response(TransferSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def send(self, request, pk):
        if not require(request.user, "create_transfers"):
            return forbidden()
        transfer = get_object_or_404(branch_queryset(Transfer.objects.select_related("source"), request.user, "source__branch"), pk=pk)
        try:
            return Response(TransferSerializer(send_transfer(transfer_id=pk, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)

    def receive(self, request, pk):
        if not require(request.user, "receive_transfers"):
            return forbidden()
        transfer = get_object_or_404(branch_queryset(Transfer.objects.select_related("destination"), request.user, "destination__branch"), pk=pk)
        try:
            return Response(TransferSerializer(receive_transfer(transfer_id=pk, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class ExpenseView(APIView):
    def get(self, request):
        qs = scoped_queryset(Expense.objects.all(), request.user)
        return Response(ExpenseSerializer(qs.order_by("-created_at"), many=True).data)

    def post(self, request, pk=None, action=None):
        if action == "approve":
            return self.approve(request, pk)
        if not require(request.user, "manage_expenses"):
            return forbidden()
        serializer = ExpenseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not in_user_branch(request.user, serializer.validated_data["branch"].pk):
            return forbidden()
        serializer.save(created_by=request.user)
        return Response(ExpenseSerializer(serializer.instance).data, status=status.HTTP_201_CREATED)

    def approve(self, request, pk):
        if not require(request.user, "approve_expenses"):
            return forbidden()
        expense = get_object_or_404(branch_queryset(Expense.objects.all(), request.user), pk=pk)
        try:
            return Response(ExpenseSerializer(approve_expense(expense=expense, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class ClosingView(APIView):
    def get(self, request, shift_id):
        shift = get_object_or_404(Shift, pk=shift_id)
        if not in_user_branch(request.user, shift.branch_id):
            return forbidden()
        return Response({"shift": shift.pk, "expected_cash": str(expected_cash_for_shift(shift))})

    def post(self, request, shift_id=None, pk=None, action=None):
        if action == "approve":
            return self.approve(request, pk)
        if not require(request.user, "manage_closing"):
            return forbidden()
        shift = get_object_or_404(Shift, pk=shift_id)
        if not in_user_branch(request.user, shift.branch_id):
            return forbidden()
        try:
            closing = create_closing(shift=shift, actual_cash=request.data.get("actual_cash", 0), user=request.user)
            return Response(ShiftClosingSerializer(closing).data, status=status.HTTP_201_CREATED)
        except (ValidationError, ValueError) as exc:
            return bad(exc)

    def approve(self, request, pk):
        if not require(request.user, "approve_closing"):
            return forbidden()
        closing = get_object_or_404(branch_queryset(ShiftClosing.objects.select_related("shift"), request.user, "shift__branch"), pk=pk)
        try:
            return Response(ShiftClosingSerializer(approve_closing(closing=closing, user=request.user)).data)
        except (ValidationError, ValueError) as exc:
            return bad(exc)


class ReportsView(APIView):
    def get(self, request, report):
        if not require(request.user, "view_reports"):
            return forbidden()
        start, end, date_from, date_to = _date_range(request)
        sales = Sale.objects.filter(status=Sale.Status.ISSUED)
        expenses = Expense.objects.filter(status=Expense.Status.APPROVED)
        if not (request.user.is_superuser or request.user.is_owner):
            sales = sales.filter(branch_id=request.user.branch_id)
            expenses = expenses.filter(branch_id=request.user.branch_id)
        sales = _filter_period(sales, "issued_at", start, end)
        expenses = _filter_period(expenses, "created_at", start, end)
        if report == "sales":
            data = {"date_from": date_from, "date_to": date_to, "invoices": sales.count(), "revenue": str(sales.aggregate(v=Sum("total"))["v"] or 0)}
        elif report == "expenses":
            data = {"date_from": date_from, "date_to": date_to, "count": expenses.count(), "total": str(expenses.aggregate(v=Sum("amount"))["v"] or 0)}
        elif report == "profit":
            revenue = sales.aggregate(v=Sum("total"))["v"] or Decimal("0")
            cogs = Sale.objects.filter(pk__in=sales.values("pk")).values("items__cogs").aggregate(v=Sum("items__cogs"))["v"] or Decimal("0")
            expense_total = expenses.aggregate(v=Sum("amount"))["v"] or Decimal("0")
            data = {"revenue": str(revenue), "cogs": str(cogs), "expenses": str(expense_total), "profit": str(revenue - cogs - expense_total)}
        elif report == "inventory":
            balances = StockBalance.objects.all()
            if not (request.user.is_superuser or request.user.is_owner):
                balances = balances.filter(location__branch_id=request.user.branch_id)
            data = {"quantity": str(balances.aggregate(v=Sum("quantity"))["v"] or 0), "value": str(sum((b.quantity * b.average_cost for b in balances), Decimal("0")))}
        else:
            return Response({"detail": "التقرير غير معروف."}, status=status.HTTP_404_NOT_FOUND)
        return Response(data)
