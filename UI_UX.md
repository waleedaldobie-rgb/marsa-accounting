# مَرسى — UI/UX Specification

## المرجع
التصميم لا يُبنى كشاشات منفصلة بلا منطق. كل شاشة يجب أن تتصل بـ Domain Service والصلاحيات والنماذج المحددة في ARCHITECTURE.md.

## Dashboard
- KPI: مبيعات اليوم، عدد الفواتير، النقد المتوقع، قيمة المخزون، التحويلات المعلقة، الهالك.
- فلتر الفرع والتاريخ بحسب الصلاحية.
- إجراءات سريعة: فتح POS، شراء، تحويل، مصروف، إغلاق وردية.

## POS
- بحث سريع عن المنتج.
- إدخال raw_weight وcleaned_weight.
- عرض unit_price والإجمالي.
- ملخص الفاتورة وpayment method.
- لا يسمح cleaned_weight > raw_weight.
- عند الإصدار تنفذ العملية عبر service واحدة atomic؛ الواجهة لا تنفذ خصم المخزون بنفسها.

## Inventory
- Stock Overview يعرض الرصيد الحالي لكل product/location.
- Movement Ledger يعرض المصدر التاريخي الرسمي.
- Adjustment لا يعدل الرصيد مباشرة؛ ينشئ حركة مع سبب واعتماد.

## Purchases
- Draft قبل الاعتماد.
- Approval واضح.
- بعد التأثير على المخزون لا حذف مباشر.
- يعرض الوزن، تكلفة الوحدة، التكلفة الإجمالية، والمورد.

## Transfers
- حالة التحويل ظاهرة.
- إرسال واستلام منفصلان.
- يعرض sent_weight وreceived_weight وdifference.
- الفرق لا يصنف هالكًا تلقائيًا.

## Closing
- يعرض Cash Sales، Approved Cash Expenses، Refunds، Adjustments، Expected Cash، Actual Cash، Difference.
- لا يمكن اعتماد الإغلاق دون الصلاحية.

## Delivery
- ربط DeliveryOrder بالفاتورة.
- Platform، commission، expected settlement، settlement status.

## UX states
كل شاشة لها:
- Loading state.
- Empty state مع إجراء مفيد إن أمكن.
- Validation state.
- Permission denied.
- Server error.
- Success feedback.

## قاعدة التنفيذ
ابدأ دائمًا بـ backend/domain contract ثم template. لا تضع قواعد الحساب في JavaScript أو template.
