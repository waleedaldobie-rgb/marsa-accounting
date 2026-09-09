# Changelog

## 2026-09-08 — Initial build
- Created Django project structure from zero.
- Configured PostgreSQL and Docker Compose.
- Added domain apps and core models.
- Added first inventory/purchase/transfer/sale services.
- Added Arabic RTL starter dashboard/login.
- Added architecture, decisions, state, handoff, sprint plan and development protocol documents.
- Added weighted-average formula test.

## Verification
- Python source passes `python -m compileall`.
- Full Django migrations/tests could not be executed in the build environment because external package installation/network access is unavailable there.
- The first local setup must run `pip install -r requirements.txt`, `makemigrations`, `migrate`, then tests.

## 2026-09-08 — UI/UX Documentation
Added the formal UI/UX reference layer: DESIGN_SYSTEM.md, SCREENS.md, NAVIGATION.md, UI_UX.md. Updated PROJECT_STATE.md so future agents must treat these as authoritative.


## v0.4 — Sprint 3
- Hardened catalog models and price-period validation.
- Added catalog forms, views, URLs and Arabic RTL screens.
- Added CSV import/template flow.
- Wired catalog navigation.
- Added Sprint 3 documentation and updated PROJECT_STATE.
- Python compileall verification passed.

- Sprint 8: raw/cleaned weight sale workflow, ProcessingRecord hardening, atomic/idempotent issue_sale, sales UI/routes.

## v0.10 — Sprint 9
- إضافة Workflow للهدر والتالف مع `WasteAdjustment` واعتماد ذري عبر `WASTE_OUT`.
- إضافة Workflow للمصاريف وربط الاعتماد بـ `PaymentTransaction` المالي.
- إضافة واجهات الهدر والمصاريف.
- تقوية محرك المخزون: تكلفة الصرف الفعلية + idempotency.
- إصلاح تحقق موقع البيع ومنع البيع من المستودع المركزي.
- إضافة اختبارات Sprint 9.


## v0.11 — Sprint 10
- إضافة دورة الإغلاق المحاسبي للورديات.
- اعتماد/رفض الإغلاق مع إغلاق الوردية عند الاعتماد.
- بناء دفتر النقدية من PaymentTransaction.
- تحديث لوحة التحكم بالمؤشرات المالية.
- حماية فتح الوردية بصلاحية open_shift.
- إضافة اختبارات الإغلاق.

## v0.12 — Sprint 11
- Added operational and financial reports.
- Added sales, inventory, waste and cash ledger reports.
- Added date filtering and sales CSV export.
- Added profitability calculations based on frozen COGS.
- Added report access permission and branch scoping.
- Added Sprint 11 report tests and documentation.

## v0.13 — Sprint 12
- استكمال المشتريات ومرتجعات المشتريات.
- إضافة دورة التوصيل والتسويات المالية.
- إضافة Audit Trail service وRequest-ID middleware.
- ربط العمليات الحساسة الجديدة بسجل التدقيق.
- تحديث التنقل والوثائق.
- Syntax check: 98 Python files / 0 errors.

## v0.13 — Sprint 13
- Hardening للصلاحيات على المبيعات.
- Sales Returns مع إعادة المخزون واسترداد مالي.
- منع تجاوز الكميات المرتجعة.
- Audit Trail موسع للعمليات الحساسة.
- تحسين حالة المصاريف وتسجيل المعتمد/الملغي.

## v0.14 — Sprint 14
- POS draft creation workflow added.
- Sales search/filter/pagination added.
- Inventory search/location filter/pagination added with branch scoping for balances and movements.
- POS raw/cleaned weight entry and live totals added.
- UAT checklist added in `docs/SPRINT_14.md`.
- Python syntax check: 0 errors.


## v0.15 — Sprint 15
- إضافة تسلسل فواتير مستقل وآمن لكل فرع مع row locking.
- استبدال UUID للفواتير بمسلسل `BRANCH-YYYYMMDD-000001`.
- إضافة automatic audit capture للطلبات التي تغيّر الحالة.
- إضافة bootstrap runtime script لتوليد/تطبيق migrations وتشغيل الاختبارات عند توفر البيئة.
- إضافة خطة اختبارات concurrency لـ PostgreSQL.
- Syntax/compile verification passed; runtime migrations/tests remain pending.

## v0.16 — Sprint 16
- ربط المصروفات النقدية بالوردية المفتوحة لضمان دخولها في حساب النقد المتوقع عند الإغلاق.
- إصلاح redirects غير صالحة في واجهة المصروفات.
- تنظيف استعلامات `Sum` في مرتجعات المبيعات.
- إضافة `/health/` لفحص جاهزية التطبيق وقاعدة البيانات.
- إضافة إعدادات أمنية قابلة للضبط عبر متغيرات البيئة.
- Syntax check: 98 Python files / 0 errors.
- ما زالت migrations وDjango/PostgreSQL runtime tests غير منفذة في بيئة البناء.


## v0.17 — Sprint 19 REST API
- Added Django REST Framework APIs under `/api/v1/`.
- Added Token Authentication and authenticated user endpoint.
- Added catalog, inventory, purchases, sales, transfers, expenses, closing and reports API resources.
- Reused existing domain services for sensitive operations and protected sensitive fields in serializers.
- Added server-side role and branch isolation checks.
- Added API tests; PostgreSQL runtime verification completed with 18 passing tests.


## Sprint 20 — Security Hardening
تم توحيد سياسات العمليات الحساسة وتطبيق عزل الفروع على مستوى الاستعلام والخدمة، مع منع كشف كائنات الفروع الأخرى عبر المعرفات المباشرة. أضيفت حماية للخدمات الحساسة والتدقيق لعمليات الإغلاق والتحويلات والهدر، وتم تشديد إعدادات Django الإنتاجية والتحقق من مرفقات المصروفات. نتيجة التحقق: 21 اختبارًا ناجحًا وفحص `check --deploy` بلا تحذيرات باستخدام secret إنتاجي طويل.


## Sprint 20 — Supplemental Security Review
تم تصحيح صلاحية الكاشير لمسار عرض تفاصيل البيع، وتقييد تعديل الكتالوج، وتشديد عزل التوصيل ومرتجعات المبيعات والهدر ومنع branch tampering. أضيف فرع صريح إلى AuditLog مع migration وربطته بالعمليات الحساسة. ارتفع الاختبار من 21 إلى 24 اختبارًا ناجحًا. الحالة النهائية المعلنة: PARTIAL بسبب عدم وجود workflow قائم مستقل للتصحيح/العكس أو شاشة/API مستقلة لإدارة سجل التدقيق والمستخدمين.


## Sprint 21 — Stock Adjustments, Audit Log & User Administration
أضيفت دورة Stock Adjustment ذرية ومقيدة بالفرع، مع API وmigration واختبارات تمنع تكرار الحركة وتعديل الرصيد مباشرة. أضيف Audit Log API وWeb UI للقراءة فقط، وإدارة مستخدمين API تحمي كلمات المرور وآخر مالك نشط. النتيجة: 31 اختبارًا ناجحًا. بقي Reversal/Correction العام غير منفذ بسبب غموض contract المحاسبي.


## Sprint 21 — UI Completion
أضيفت واجهات Django Templates لتسويات المخزون، Audit Log، وإدارة المستخدمين، مع ربطها بالمسارات والتنقل وفرض الصلاحيات من الخادم. أضيفت اختبارات Web UI، وأصبح مجموع الاختبارات 34 ناجحًا. بقيت Correction/Reversal غير منفذة بسبب غياب contract محاسبي موحد.
