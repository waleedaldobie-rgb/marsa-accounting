# Sprint 21 Result — Stock Adjustments, Audit Log & User Administration

## Security

**🟢** أضيف workflow server-side لتسويات المخزون، مع منع تعديل `StockBalance` مباشرة من View أو API. تعتمد التسوية على `StockMovement`، وتستخدم `transaction.atomic()` و`select_for_update()` عند الاعتماد. كما تم منع الاعتماد خارج فرع المستخدم، ومنع الاعتماد عند تغير الرصيد منذ إنشاء التسوية.

**🟡** لم يتم اختراع workflow مالي عام للعكس أو التصحيح. الكود الحالي يمنع نشر حركة `CORRECTION` مباشرة، لكنه لا يثبت قواعد عكس موحدة للمبيعات والمشتريات والمصروفات والتحويلات. لذلك بقي هذا الجزء خارج التنفيذ حتى لا يُنشأ منطق محاسبي غير معتمد.

## Permissions

**🟢** أضيفت سياسات `can_create_adjustment` و`can_approve_adjustment` و`can_manage_users`، مع الحفاظ على الأدوار الحالية فقط. لا يستطيع مدير الفرع إنشاء مالك أو superuser، ولا يستطيع تعديل نفسه إلى صلاحيات أعلى.

## Stock Adjustments

**🟢** تمت إضافة `StockAdjustment` و`StockAdjustmentItem` بالحالات `DRAFT` و`APPROVED` و`CANCELLED`. المسودة لا تؤثر على المخزون. الاعتماد ينشئ `ADJUSTMENT_IN` أو `ADJUSTMENT_OUT` عبر `apply_movement`، ويحفظ `system_quantity` و`counted_quantity` و`difference`. لا يمكن اعتماد التسوية بلا سبب أو بلا أصناف، ولا يمكن تعديل تسوية معتمدة.

## Reversal / Correction

**🟡** لم يُنفذ Reversal عام في هذه الجولة. السبب أن الخدمات الحالية لا توفر contract موحدًا لعكس Sale/Purchase/Transfer/Expense/Waste، والعكس قد يؤثر على المخزون والمال والدفتر. تم توثيق القيد بدل اختراع قواعد جديدة.

## Audit Log

**🟢** أضيفت واجهة API للقراءة فقط تحت `/api/v1/audit/` مع تصفية المستخدم والفرع والإجراء والكيان والتاريخ. أضيفت صفحة ويب تحت `/audit/` مع pagination وempty state. المستخدم العادي لا يصل للسجل، والمحاسب يرى نطاق فرعه، والمالك يرى جميع الفروع. لا توجد عمليات POST أو PATCH أو DELETE للسجل.

## User Administration

**🟢** أضيفت API إدارة المستخدمين تحت `/api/v1/users/` و`/api/v1/users/<id>/`. يدعم النطاق الحالي العرض والإنشاء والتعديل وتفعيل/تعطيل المستخدم وتغيير كلمة المرور عبر `set_password`. لا تظهر كلمة المرور في الاستجابة أو التدقيق، ولا يمكن تعديل `is_superuser` أو `is_staff` من الطلب. تمت حماية آخر مالك نشط من التعطيل.

## Branch Isolation

**🟢** تسويات المخزون وسجل التدقيق وإدارة المستخدمين مقيدة server-side بنطاق الفرع. لا يمكن لفرع A اعتماد تسوية فرع B أو قراءة سجل تدقيق فرع B. عند إنشاء التسوية يستنتج الفرع من الموقع المرتبط بفرع المستخدم، ولا يثق النظام في `branch` المرسل من العميل.

## API Security

**🟢** تمت إضافة مسارات:

```text
GET/POST /api/v1/inventory/adjustments/
GET /api/v1/inventory/adjustments/<id>/
POST /api/v1/inventory/adjustments/<id>/approve/
POST /api/v1/inventory/adjustments/<id>/cancel/
GET /api/v1/audit/
GET/POST /api/v1/users/
GET/PATCH /api/v1/users/<id>/
```

الحقول المحسوبة أو الحساسة مثل `branch` و`status` و`created_by` و`approved_by` و`system_quantity` و`difference` وحقول التدقيق للقراءة فقط أو تُحدد من الخادم.

## Transactions and Concurrency

**🟢** اعتماد التسوية يستخدم `transaction.atomic()`، ويقفل التسوية والأرصدة ذات الصلة باستخدام `select_for_update()`. كما يمنع reference id تكرار حركة المخزون، ويجعل الاعتماد الثاني idempotent دون إنشاء حركة ثانية.

## Tests

عدد الاختبارات قبل Sprint 21: **24**.

عدد الاختبارات بعد Sprint 21: **31**.

عدد الناجحة: **31**.

عدد الفاشلة: **0**.

تم تشغيلها فعليًا داخل Docker/PostgreSQL، وشملت:

- Adjustment lifecycle.
- عدم تأثير المسودة على المخزون.
- الاعتماد المكرر دون تكرار الحركة.
- رفض الفرع الخطأ.
- رفض الرصيد المتغير منذ إنشاء التسوية.
- Audit API authentication وimmutability.
- إنشاء مستخدم دون كشف كلمة المرور.
- حماية آخر مالك نشط.

## Verification Evidence

```text
python manage.py migrate: inventory.0002 applied successfully
python manage.py check: OK
pytest -q: 31 passed
python -m compileall -q api apps config: OK
```

## Changed Files

تم تعديل `apps/accounts/permissions.py` و`apps/inventory/models.py` و`apps/inventory/adjustment_services.py`، وإضافة `apps/inventory/migrations/0002_stockadjustment_stockadjustmentitem.py`.

تم تعديل `api/serializers.py` و`api/views.py` و`api/urls.py`، وإضافة `apps/inventory/test_sprint21.py`.

تمت إضافة Audit UI عبر `apps/audit/views.py` و`apps/audit/urls.py` و`templates/audit/list.html`، وربطه في `config/urls.py`.

## Security Findings

| المستوى | النتيجة |
|---|---|
| Critical | لا توجد ثغرة حرجة في النطاق المنفذ. |
| High | تمت معالجة تعديل StockBalance المباشر، اعتماد التسوية خارج الفرع، تكرار حركة التسوية، كشف كلمة المرور، وتعطيل آخر مالك. |
| Medium | Reversal/Correction العام غير منفذ لعدم وجود قواعد محاسبية موحدة مثبتة في الكود. |
| Low | لا توجد واجهة ويب مستقلة لإدارة المستخدمين؛ الإدارة متاحة عبر API، بينما Audit Log له API وWeb UI. |

## Final Decision

**SPRINT 21: 🟡 PARTIAL**

السبب: تم تنفيذ تسويات المخزون وسجل التدقيق وإدارة المستخدمين واختبارها، لكن Reversal/Correction العام بقي خارج النطاق التنفيذي بسبب غموض قواعده المالية في النظام الحالي.

### Recommended Next Step

**Sprint 22 فقط:** اعتماد وتنفيذ contract محاسبي موحد للتصحيح والعكس، ثم إضافة workflow خاص بالمستندات التي يثبت دعمها من الخدمات الحالية. لا يبدأ تلقائيًا.


## UI Completion Review — Supplemental Requirement

تمت إضافة وربط واجهات Django Templates التالية باستخدام `base.html` ونظام التصميم الحالي:

| الشاشة | Template | URL | View | Permission | Status |
|---|---|---|---|---|---|
| Stock Adjustments List | `templates/inventory/adjustments/list.html` | `/inventory/adjustments/` | `adjustment_list` | `manage_adjustments` | DONE |
| Create Adjustment | `templates/inventory/adjustments/form.html` | `/inventory/adjustments/new/` | `adjustment_create` | `manage_adjustments` | DONE |
| Adjustment Detail | `templates/inventory/adjustments/detail.html` | `/inventory/adjustments/<id>/` | `adjustment_detail` | `manage_adjustments` | DONE |
| Audit Log List | `templates/audit/list.html` | `/audit/` | `audit_list` | OWNER/ACCOUNTANT | DONE |
| Audit Detail | `templates/audit/detail.html` | `/audit/<id>/` | `audit_detail` | OWNER/ACCOUNTANT | DONE |
| Users | `templates/accounts/users/list.html` | `/accounts/users/` | `user_list` | OWNER/superuser | DONE |
| User Create/Edit | `templates/accounts/users/form.html` | `/accounts/users/new/`, `/accounts/users/<id>/edit/` | `user_create`, `user_edit` | OWNER/superuser | DONE |
| User Detail | `templates/accounts/users/detail.html` | `/accounts/users/<id>/` | `user_detail` | OWNER/superuser | DONE |
| Correction/Reversal | — | — | — | — | NOT IMPLEMENTED |

واجهات التسوية تشمل قائمة، إنشاء مسودة، التفاصيل، timeline مبسط للحالة، حركة المخزون الناتجة، اعتمادًا بتأكيد JavaScript، وإلغاءً يتطلب سببًا. واجهات Audit Log للقراءة فقط، وتحتوي على pagination وfilters وصفحة تفاصيل. واجهات المستخدمين تشمل القائمة والإنشاء والتعديل والتفاصيل وسجل النشاط.

تم تحديث Sidebar لإظهار تسويات المخزون لمدير الفرع والمحاسب والمالك، وإظهار Audit Log للمحاسب والمالك، وإظهار المستخدمين للمالك فقط. الإخفاء ليس طبقة حماية؛ كل View يفرض الصلاحية وعزل الفرع server-side.

عدد الاختبارات قبل إضافة واجهات Sprint 21: **31**.

عدد الاختبارات بعد إضافة الواجهات: **34**.

عدد الناجحة: **34**.

عدد الفاشلة: **0**.

أضيفت اختبارات Django test client للتحقق من وصول مدير الفرع إلى واجهات التسوية، منع الكاشير، وصول المالك إلى Audit Log وإدارة المستخدمين، وإنشاء مسودة تسوية من الويب.

## Updated Final Decision

**SPRINT 21: 🟡 PARTIAL**

تم الآن استكمال الواجهات الفعلية للتسويات والتدقيق وإدارة المستخدمين. يبقى الجزء غير المنفذ هو Correction/Reversal، لأن المشروع لا يقدم contract محاسبيًا موحدًا لعكس المستندات المالية والمخزنية. لا توجد أزرار أو صفحات وهمية لهذا الجزء.
