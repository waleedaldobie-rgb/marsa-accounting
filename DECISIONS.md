# Architecture Decisions

## ADR-001 — PostgreSQL
PostgreSQL هي قاعدة البيانات الأساسية المعتمدة. SQLite ليست بديلًا للتشغيل الطبيعي.

## ADR-002 — Inventory source of truth
StockMovement هو السجل الرسمي لكل تغيير. StockBalance رصيد مشتق سريع ولا يجوز تعديله مباشرة.

## ADR-003 — Weighted Average Cost
التكلفة المتوسطة المرجحة تُحسب عند الإدخال وتُستخدم لتثبيت تكلفة الخروج التاريخية. لا تعاد كتابة COGS القديمة بناءً على التكلفة الحالية.

## ADR-004 — Raw vs Cleaned Weight
المخزون يخرج بالوزن الخام، والفاتورة تُحسب بالوزن المنظف. فرق الوزن يسجل في ProcessingRecord ولا يتحول تلقائيًا إلى Waste.

## ADR-005 — Financial ledger
الإغلاق لا يعتمد على مقارنة أرقام متناثرة؛ يجب أن يبنى على PaymentTransaction وحركات المال المعتمدة.

## ADR-006 — Reversal over deletion
المستندات المؤثرة على المخزون/المال لا تُحذف بعد اعتمادها. التصحيح يتم بعكس/تصحيح موثق.

## ADR-007 — Domain services
العمليات الحساسة تنفذ من خدمات الدومين، وليس من template/JS أو الاعتماد الوحيد على Model.save().
