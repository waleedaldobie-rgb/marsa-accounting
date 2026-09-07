# Architecture — مَرسى

## طبقات النظام
1. Models: تمثيل البيانات والقيود الأساسية فقط.
2. Domain Services: العمليات التي تغير المخزون/المال/الحالة.
3. Permissions: صلاحيات الدور ونطاق الفرع على الخادم.
4. Views/API: استقبال الطلب والتحقق واستدعاء الخدمات.
5. UI: عرض البيانات فقط ولا يحتوي منطقًا محاسبيًا.
6. Reports: قراءة دفتر الحركات والمعاملات التاريخية.

## اتجاه الاعتماد
`UI -> Views/API -> Services -> Models`

الخدمات المركزية المقصودة:
- `inventory.services.apply_movement`
- `purchases.services.approve_purchase`
- `transfers.services.send_transfer`
- `transfers.services.receive_transfer`
- `sales.services.issue_sale_item`

## المخزون
`StockMovement` هو المصدر الرسمي للحركات. `StockBalance` cache/aggregate سريع.

أنواع الحركة: PURCHASE_IN, TRANSFER_OUT, TRANSFER_IN, SALE_OUT, WASTE_OUT, ADJUSTMENT_IN, ADJUSTMENT_OUT, PURCHASE_RETURN, SALES_RETURN, CORRECTION.

## التكلفة
`new_average = ((old_qty * old_cost) + (new_qty * new_cost)) / (old_qty + new_qty)`.
عند البيع: `COGS = raw_weight * unit_cost_at_sale`.
التحويل يحمل تكلفة المصدر.

## البيع
`raw_weight` يخص خروج المخزون.
`cleaned_weight` يخص الكمية المفوترة.
`sale_amount = cleaned_weight * unit_price`.
`processing_difference = raw_weight - cleaned_weight`.

## المال
`PaymentTransaction` دفتر تدفقات مالية أولي، وسيُستكمل ربطه بالإغلاق والتسويات والمصروفات.

## الأمان
لا تعتمد على إخفاء الأزرار في الواجهة. كل عملية حساسة يجب أن تتحقق من المستخدم والدور والفرع على الخادم، وأن تُسجل في AuditLog.
