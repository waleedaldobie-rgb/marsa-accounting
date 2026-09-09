from rest_framework import serializers
from apps.accounts.models import User

from apps.branches.models import Branch, Location
from apps.catalog.models import Product, ProductPrice, Supplier
from apps.closing.models import ShiftClosing
from apps.expenses.models import Expense
from apps.inventory.models import StockAdjustment, StockAdjustmentItem, StockBalance, StockMovement
from apps.audit.models import AuditLog
from apps.purchases.models import Purchase, PurchaseItem, PurchaseReturn, PurchaseReturnItem
from apps.sales.models import Sale, SaleItem, SalesReturn, SalesReturnItem, Shift
from apps.transfers.models import Transfer, TransferItem


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = ("id", "code", "name", "is_active")


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ("id", "name", "kind", "branch", "is_active")


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ("id", "name", "phone", "notes", "is_active", "created_at", "updated_at")
        read_only_fields = ("id", "created_at", "updated_at")


class ProductPriceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPrice
        fields = ("id", "product", "price", "starts_at", "ends_at", "created_at")
        read_only_fields = ("id", "created_at")


class ProductSerializer(serializers.ModelSerializer):
    current_price = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ("id", "name", "sku", "unit", "description", "is_active", "current_price", "created_at", "updated_at")
        read_only_fields = ("id", "unit", "current_price", "created_at", "updated_at")

    def get_current_price(self, obj):
        price = obj.current_price
        return str(price.price) if price else None


class StockBalanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockBalance
        fields = ("id", "product", "location", "quantity", "average_cost", "updated_at")
        read_only_fields = fields


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = ("id", "product", "location", "movement_type", "quantity", "unit_cost", "total_cost", "reference_type", "reference_id", "reason", "created_by", "created_at")
        read_only_fields = fields


class StockAdjustmentItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    counted_quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    reason = serializers.CharField(required=False, allow_blank=True)


class StockAdjustmentItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockAdjustmentItem
        fields = ('id', 'product', 'system_quantity', 'counted_quantity', 'difference', 'reason')
        read_only_fields = fields


class StockAdjustmentSerializer(serializers.ModelSerializer):
    items = StockAdjustmentItemInputSerializer(many=True, write_only=True, required=False)
    item_records = StockAdjustmentItemSerializer(source='items', many=True, read_only=True)

    class Meta:
        model = StockAdjustment
        fields = ('id', 'branch', 'location', 'status', 'reason', 'created_by', 'approved_by', 'created_at', 'approved_at', 'cancelled_at', 'items', 'item_records')
        read_only_fields = ('id', 'branch', 'status', 'created_by', 'approved_by', 'created_at', 'approved_at', 'cancelled_at', 'item_records')


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = ('id', 'user', 'branch', 'action', 'entity', 'entity_id', 'old_value', 'new_value', 'reason', 'request_id', 'ip_address', 'created_at')
        read_only_fields = fields


class UserAdminSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 'role', 'branch', 'is_active', 'password')
        read_only_fields = ('id',)

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'كلمة المرور مطلوبة.'})
        user = self.Meta.model(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for field, value in validated_data.items():
            setattr(instance, field, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class PurchaseItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=0)


class PurchaseSerializer(serializers.ModelSerializer):
    items = PurchaseItemInputSerializer(many=True, write_only=True, required=False)
    item_records = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Purchase
        fields = ("id", "supplier", "location", "invoice_no", "status", "total", "created_by", "approved_by", "created_at", "items", "item_records")
        read_only_fields = ("id", "status", "total", "created_by", "approved_by", "created_at", "item_records")

    def get_item_records(self, obj):
        return [{"product": item.product_id, "quantity": str(item.quantity), "unit_cost": str(item.unit_cost)} for item in obj.items.all()]

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        purchase = Purchase.objects.create(**validated_data)
        PurchaseItem.objects.bulk_create([PurchaseItem(purchase=purchase, **item) for item in items])
        return purchase


class PurchaseReturnItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    unit_cost = serializers.DecimalField(max_digits=14, decimal_places=4, min_value=0)


class PurchaseReturnSerializer(serializers.ModelSerializer):
    items = PurchaseReturnItemInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = PurchaseReturn
        fields = ("id", "purchase", "location", "reference_no", "status", "total", "reason", "created_by", "approved_by", "created_at", "approved_at", "items")
        read_only_fields = ("id", "status", "total", "created_by", "approved_by", "created_at", "approved_at")

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        ret = PurchaseReturn.objects.create(**validated_data)
        PurchaseReturnItem.objects.bulk_create([PurchaseReturnItem(purchase_return=ret, **item) for item in items])
        return ret


class ShiftSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shift
        fields = ("id", "branch", "cashier", "opening_cash", "status", "opened_at", "closed_at")
        read_only_fields = ("id", "cashier", "status", "opened_at", "closed_at")


class SaleItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    raw_weight = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    cleaned_weight = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)
    unit_price = serializers.DecimalField(max_digits=14, decimal_places=2, min_value=0)

    def validate(self, attrs):
        if attrs["cleaned_weight"] > attrs["raw_weight"]:
            raise serializers.ValidationError("cleaned_weight لا يمكن أن يتجاوز raw_weight.")
        if attrs["raw_weight"] <= 0 or attrs["cleaned_weight"] <= 0:
            raise serializers.ValidationError("الأوزان يجب أن تكون أكبر من صفر.")
        return attrs


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemInputSerializer(many=True, write_only=True, required=False)
    item_records = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Sale
        fields = ("id", "invoice_no", "shift", "branch", "channel", "status", "total", "created_by", "created_at", "issued_at", "issued_by", "items", "item_records")
        read_only_fields = ("id", "invoice_no", "branch", "status", "total", "created_by", "created_at", "issued_at", "issued_by", "item_records")

    def get_item_records(self, obj):
        return [{"product": item.product_id, "raw_weight": str(item.raw_weight), "cleaned_weight": str(item.cleaned_weight), "unit_price": str(item.unit_price), "sale_amount": str(item.sale_amount), "cogs": str(item.cogs)} for item in obj.items.all()]


class TransferItemInputSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    sent_quantity = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)


class TransferSerializer(serializers.ModelSerializer):
    items = TransferItemInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Transfer
        fields = ("id", "source", "destination", "status", "note", "created_by", "sent_at", "received_at", "items")
        read_only_fields = ("id", "status", "created_by", "sent_at", "received_at")

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        transfer = Transfer.objects.create(**validated_data)
        TransferItem.objects.bulk_create([TransferItem(transfer=transfer, **item) for item in items])
        return transfer


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ("id", "branch", "shift", "category", "amount", "payment_method", "status", "attachment", "created_by", "created_at", "approved_by", "approved_at", "cancelled_at")
        read_only_fields = ("id", "status", "created_by", "created_at", "approved_by", "approved_at", "cancelled_at")

    def validate_attachment(self, attachment):
        if not attachment:
            return attachment
        allowed = (".pdf", ".jpg", ".jpeg", ".png")
        if not attachment.name.lower().endswith(allowed):
            raise serializers.ValidationError("نوع الملف غير مسموح.")
        if attachment.size > 5 * 1024 * 1024:
            raise serializers.ValidationError("حجم الملف يجب ألا يتجاوز 5 ميجابايت.")
        return attachment


class ShiftClosingSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShiftClosing
        fields = ("id", "shift", "expected_cash", "actual_cash", "difference", "status", "approved_by", "created_at", "approved_at")
        read_only_fields = ("id", "expected_cash", "difference", "status", "approved_by", "created_at", "approved_at")


class SalesReturnItemInputSerializer(serializers.Serializer):
    sale_item = serializers.PrimaryKeyRelatedField(queryset=SaleItem.objects.all())
    raw_weight = serializers.DecimalField(max_digits=14, decimal_places=3, min_value=0)


class SalesReturnSerializer(serializers.ModelSerializer):
    items = SalesReturnItemInputSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = SalesReturn
        fields = ("id", "sale", "branch", "reason", "refund_amount", "status", "payment_method", "created_by", "approved_by", "created_at", "approved_at", "cancelled_at", "items")
        read_only_fields = ("id", "branch", "refund_amount", "status", "created_by", "approved_by", "created_at", "approved_at", "cancelled_at")

    def create(self, validated_data):
        items = validated_data.pop("items", [])
        ret = SalesReturn.objects.create(**validated_data)
        SalesReturnItem.objects.bulk_create([SalesReturnItem(sales_return=ret, **item) for item in items])
        return ret
