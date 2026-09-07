# PROJECT STATE — اقرأني أولًا

آخر تحديث: 2026-09-08

## الهدف
بناء نظام ERP/POS باسم **مَرسى** لمحلات الأسماك، يدير موردين ومشتريات ومخزون وفروع ومبيعات ووزن خام/منظف ومصاريف وإغلاق ورديات وتوصيل وتقارير وتدقيق.

## ما تم بناؤه الآن
- مشروع Django من الصفر.
- PostgreSQL configuration + Docker Compose.
- Custom User مع Role وBranch.
- Branch وLocation.
- Supplier وProduct وProductPrice.
- StockMovement وStockBalance.
- Purchase/PurchaseItem.
- Transfer/TransferItem.
- Shift/Sale/SaleItem/PaymentTransaction.
- ProcessingRecord.
- Delivery Platform/DeliveryOrder/Settlement.
- Expense.
- ShiftClosing.
- AuditLog.
- خدمات مخزون/شراء/تحويل/بيع أولية تستخدم `transaction.atomic` و`select_for_update` في العمليات الحساسة.
- لوحة تحكم أولية وhealth endpoint.
- اختبار صيغة Weighted Average Cost.

## ما لم يُعتبر مكتملًا بعد
- migrations الناتجة فعليًا من بيئة التشغيل.
- نظام permissions/scoping الكامل لكل endpoint/view.
- approval workflows كاملة لكل المستندات.
- purchase returns وsales returns كاملة كخدمات.
- WasteAdjustment ككيان workflow كامل.
- Expense service وربطه بدفتر المال.
- Shift closing service والصيغة النهائية لكل طرق الدفع.
- Delivery settlement service.
- invoice sequencing/idempotency production-grade.
- Audit middleware/automatic capture.
- التقارير النهائية وCSV.
- واجهات التشغيل الكاملة.
- اختبارات التكامل والتزامن والـUAT.
- backup/restore test.

## القرار الحالي
لا توسع النطاق ولا تعيد تصميم الدومين دون تحديث هذا الملف و`DECISIONS.md`.

## Sprint 3 progress — implemented after Sprint 2
- Product/Supplier/ProductPrice master data hardened.
- KG enforced as the product base unit.
- Price period validation prevents overlapping intervals.
- Product/supplier CRUD screens and product price history screen added.
- CSV product import + downloadable template added.
- Catalog navigation wired into the RTL ERP shell.
- Sprint documentation added at `docs/SPRINT_3.md`.

### Not yet verified
- Django migrations/runtime tests still require an installed Django + PostgreSQL environment.
- Full object-level permission integration remains a cross-sprint hardening task.

## Sprint 8 progress — implemented
- Raw/cleaned weight rules and atomic sale issue service implemented.
- Stock-out uses raw weight; sale amount uses cleaned weight.
- COGS is frozen from average cost at issue time.
- ProcessingRecord stores cleaning difference.
- One payment transaction per issued sale with unique sale reference.
- Sales screens and routes added.

## الخطوة التالية
Sprint 9: WasteAdjustment workflow + Expense service and financial ledger integration.

## قاعدة الاستمرارية
أي محرر/وكيل جديد يجب أن:
1. يقرأ `PROJECT_STATE.md`.
2. يقرأ `ARCHITECTURE.md`.
3. يقرأ `DECISIONS.md`.
4. يفحص الكود الحالي قبل التعديل.
5. ينفذ Sprint واحدًا فقط.
6. يشغل الاختبارات/الفحوصات المتاحة.
7. يحدث هذا الملف بما تم وما بقي.
8. لا يدعي اكتمال شيء لم يتم اختباره.

## UI/UX Documentation Added
- DESIGN_SYSTEM.md: visual system and component rules.
- SCREENS.md: official screen registry.
- NAVIGATION.md: roles and navigation/permission map.
- UI_UX.md: behavior specification for major screens and UX states.

These files are authoritative design references. A future agent must read them before implementing or changing UI.

## Sprint 2 progress — implemented in v0.3
- Added explicit role permission map in `apps/accounts/permissions.py`.
- Added server-side branch queryset scoping helpers and same-branch validation helper.
- Added role convenience properties to `User`.
- Added validation to `Location` for central warehouse vs branch semantics.
- Added `seed_marsa` management command for 2 branches + central warehouse without default passwords.
- Added Arabic RTL ERP shell, sidebar, topbar, dashboard, and login screen according to the documented design system.

### Not yet verified
- Django migrations and runtime tests require a working Django/PostgreSQL environment.
- Full object-level permission integration into every view/service remains a Sprint 2 follow-up.

## Sprint 9 status
- WasteAdjustment: implemented.
- Expense approval/cancel service: implemented.
- Payment ledger OUT for approved expenses: implemented.
- Waste and expense UI routes/templates: implemented.
- Inventory movement hardening: implemented.
- Sales location validation hardened: branch warehouse only.
- Runtime Django/PostgreSQL tests: NOT RUN in build environment; migrations still need to be generated/applied locally.


## آخر تحديث — Sprint 10
تم تنفيذ دورة الإغلاق المحاسبي ودفتر النقدية: ShiftClosing، احتساب النقد المتوقع من PaymentTransaction، اعتماد وإغلاق الوردية ذريًا، رفض المسودة، نطاق الفروع، صفحة دفتر النقدية، وربط مؤشرات اللوحة بالمبيعات والمصاريف والورديات المفتوحة. تمت إضافة اختبارات Sprint 10. لم تُشغّل اختبارات Django/PostgreSQL الفعلية لعدم توفر runtime في بيئة البناء؛ تم فحص Syntax لجميع ملفات Python.

## Sprint 11 — Current
التقارير التشغيلية والمالية أصبحت موجودة تحت `apps/reports`: dashboard، sales، inventory، waste، ledger، وتصدير CSV للمبيعات. التقارير تعتمد على المستندات المعتمدة فقط وتطبق branch scoping. الربحية تعتمد على `SaleItem.cogs` المجمد وقت البيع.

### Next
Sprint 12: استكمال المشتريات/التوريد والمرتجعات والتوصيل وربطها بالتقارير والـ audit trail.

## Sprint 12 — Current
تم استكمال المشتريات ومرتجعاتها كدورة تشغيلية، وإضافة إدارة التوصيل والتسويات وربطها بالدفتر المالي، وإضافة Audit Trail service وrequest-id middleware وتسجيل العمليات الحساسة التي تم لمسها في هذا الـSprint. تم تحديث التنقل. فحص Syntax: 98 ملف Python، 0 أخطاء. ما زالت migrations واختبارات Django/PostgreSQL runtime غير منفذة في بيئة البناء.

### Next
Sprint 13: hardening شامل للصلاحيات وAudit Trail، مرتجعات المبيعات والعملاء، وتحسين POS/UX واختبارات التكامل/UAT.


## Sprint 13 completed
تم تنفيذ Hardening + Sales Returns + توسيع Audit Trail. النسخة الحالية: v0.13.

### Next
Sprint 14: اختبارات تكامل/UAT، تحسين POS الحقيقي، pagination/search/filter، ثم تجهيز migrations بعد توفر Django/PostgreSQL runtime.

## Sprint 14 — Current
تم تحسين POS ليُنشئ مسودة فاتورة من وردية مفتوحة دون أثر على المخزون أو دفتر المال حتى الإصدار. تمت إضافة بحث/فلترة/pagination للمبيعات، وبحث/فلترة/pagination للمخزون، وتقوية branch scoping لحركات المخزون، وإضافة UAT checklist.

### Verification
- `compileall`: 0 أخطاء Syntax.
- Django/PostgreSQL runtime tests: NOT RUN.
- Migrations: لم تُنشأ/تُطبق بالكامل بعد.

### Next
Sprint 15 completed: runtime bootstrap helper + invoice sequencing + automatic audit capture + concurrency test plan. Runtime migration generation/application and PostgreSQL concurrency tests remain pending until a real Django/PostgreSQL environment is available.


## Sprint 15 — Current
- Added branch-scoped InvoiceSequence with row locking.
- Draft invoice numbers now use sequential branch/date numbering instead of UUIDs.
- Added automatic audit entries for successful state-changing HTTP requests; domain audit events remain authoritative for sensitive actions.
- Added `scripts/bootstrap_runtime.py` for check/makemigrations/migrate/test in a real environment.
- Added PostgreSQL concurrency test plan.
- Runtime migrations/tests: NOT RUN in build environment.

### Next
Sprint 16: production-ready migrations after runtime verification, backup/restore rehearsal, observability, and final UAT gate.

## Sprint 16 — Current
تم تنفيذ Hardening تشغيلي مهم قبل مرحلة الـruntime: ربط المصروف النقدي بالوردية المفتوحة حتى يدخل `PaymentTransaction.OUT` في حساب إغلاق الوردية، إصلاح أخطاء redirects في المصروفات، تنظيف استعلامات مرتجعات المبيعات، وإضافة `/health/` لفحص التطبيق وقاعدة البيانات. كما تمت إضافة إعدادات أمنية قابلة للضبط عبر البيئة.

### Verification
- `python -m compileall -q .`: 0 أخطاء.
- Django/PostgreSQL runtime: غير منفذ في بيئة البناء.
- migrations: لم تُنشأ/تُطبق بعد.

### Next
المرحلة التالية ليست إضافة ميزات عشوائية: تشغيل runtime حقيقي، إنشاء ومراجعة migrations، تنفيذ الاختبارات، ثم backup/restore وUAT النهائي، مع إصلاح أي أخطاء runtime تظهر فعليًا.


## Sprint 19 — REST API
- تمت إضافة Django REST Framework تحت `/api/v1/`.
- تمت إضافة Token Authentication ونقطة `/api/v1/auth/token/` ونقطة `/api/v1/me/`.
- تمت إضافة APIs للكتالوج والأسعار والموردين والفروع والمواقع والمخزون والمشتريات ومرتجعاتها والورديات والمبيعات ومرتجعاتها والتحويلات والمصروفات والإغلاق والتقارير.
- عمليات التغيير الحساسة تمر عبر خدمات الدومين الحالية، ولا تسمح serializers بتعديل `invoice_no` أو `status` أو `total` أو `cogs` أو حقول الاعتماد والتدقيق.
- تم تطبيق عزل الفروع والتحقق من الدور والملكية والصلاحيات على الخادم.
- تمت إضافة اختبارات API للمصادقة والصلاحيات وعزل الفروع والتحقق والبيع والمخزون.

### Verification
- `python manage.py check`: OK.
- PostgreSQL migrations داخل Docker: لا توجد migrations معلقة.
- `pytest -q`: 18 passed.
- لا تشمل هذه المرحلة OpenAPI أو refresh tokens أو rate limiting أو pagination موحد.

### Next
Sprint 20 يجب أن يحدد صراحة قبل التنفيذ؛ لا توسع نطاق REST API تلقائيًا.
