# Sprint 20 Result — Security, Permissions, Authorization & Branch Isolation

## Security

**🟢** تم تشديد `DEBUG` و`SECRET_KEY` وCSRF origins وsecure cookies وHSTS وX-Frame-Options وReferrer Policy. كما تم تقييد مرفقات المصروفات إلى PDF/JPG/PNG وبحد أقصى 5MB. فحص `check --deploy` نجح باستخدام secret إنتاجي طويل.

## Permissions

**🟢** أضيفت سياسات مركزية للعمليات الحساسة، وتم تصحيح تناقض الكاشير بإضافة `view_sales` إلى صلاحياته، مع إبقاء صلاحياته التشغيلية محدودة. أصبحت كتابة الكتالوج متاحة فقط لمن لديه `manage_catalog`؛ مدير الفرع لا يكتسب صلاحية تعديل الكتالوج لمجرد امتلاكه `view_catalog`.

## Branch Isolation

**🟢** تم تطبيق object-level scoping قبل القراءة وقبل العمليات الحساسة في المبيعات والمشتريات والمصروفات والهدر والإغلاق والتوصيل وواجهات API. تغيير `branch_id` في POST لا يغيّر فرع العملية؛ الفرع يستنتج من المستخدم أو الوردية أو المستند. الوصول إلى كائن فرع آخر عبر معرف مباشر يعيد `404` في المسارات المقيدة.

## API Security

**🟢** نقاط API تتطلب Token Authentication، والحقول الحساسة مثل `created_by` و`approved_by` و`status` و`total` و`invoice_no` و`cogs` للقراءة فقط. تمت تغطية الطلب المجهول، الدور غير المسموح، الفرع الخطأ، object access، unauthorized POST، وتلاعب `branch` في الاختبارات. عمليات PATCH/DELETE غير المعرفة لا تنفذ mutation وتعيد `405`، وPATCH المنتج محمي بصلاحية الإدارة.

## Audit

**🟢** أضيف حقل `branch` صريح إلى `AuditLog` عبر migration `audit.0002_auditlog_branch`. أصبحت العمليات الحساسة تمرر فرع الكائن إلى التدقيق، بما يشمل البيع والمرتجع والمصروف والهدر والشراء والتحويل والإغلاق والتوصيل. السجل يحتوي actor وaction وobject وtimestamp وreason وbefore/after عند الحاجة، ولا يسجل الأسرار.

## Transactions

**🟢** العمليات متعددة الخطوات الموجودة أصلًا تستخدم `transaction.atomic()`، بما يشمل إصدار البيع، اعتماد الشراء، التحويلات، المصروفات، الهدر، التوصيل والإغلاق. لم يتم نقل منطق الأعمال إلى templates أو serializers.

## Concurrency

**🟢** بقي `select_for_update()` في أرصدة المخزون والوردية والمستندات ومسار إصدار البيع والتحويل والاستلام والإغلاق، مع تطبيق migration داخل PostgreSQL بنجاح.

## Tests

عدد الاختبارات قبل هذه الجولة: **21**.

عدد الاختبارات بعد هذه الجولة: **24**.

عدد الناجحة: **24**.

عدد الفاشلة: **0**.

شملت الاختبارات authentication، role escalation، cashier workflow، branch isolation، direct object access، branch tampering، unauthorized POST، إصدار البيع، والتوصيل عبر فرع آخر.

## Changed Files

تم تعديل `apps/accounts/permissions.py` لتوحيد السياسات وعزل الفرع، و`apps/sales/views.py` و`apps/sales/services.py` و`apps/sales/return_views.py` و`apps/sales/return_services.py` لحماية المبيعات والمرتجعات ومسار الكاشير. تم تعديل `apps/purchases/views.py` و`apps/purchases/services.py` و`apps/transfers/services.py` و`apps/closing/services.py` و`apps/expenses/views.py` و`apps/expenses/services.py` لحماية العمليات والاعتماد والتدقيق.

تم تعديل `apps/inventory/waste_views.py` و`apps/inventory/waste_services.py` لحماية الهدر وإصلاح redirect غير معرف، و`apps/delivery/views.py` و`apps/delivery/services.py` لعزل التوصيل وتسوية الدفعات، و`apps/catalog/views.py` لتقييد صلاحيات الكتابة. تم تعديل `api/views.py` و`api/serializers.py` و`api/tests.py` و`config/settings.py` و`.env.example`، وإضافة حقل الفرع إلى `apps/audit/models.py` و`apps/audit/services.py` مع migration `apps/audit/migrations/0002_auditlog_branch.py`.

## Security Findings

| المستوى | الحالة |
|---|---|
| Critical | لا توجد ثغرة حرجة متبقية ضمن المسارات التي تم فحصها. |
| High | تمت معالجة تجاوز الفرع عبر URL/API وPOST tampering وإصدار بيع فرع آخر. |
| Medium | لا يوجد workflow فعلي مستقل لـ stock adjustment أو reversal/correction في الكود الحالي؛ النظام يمنع حركة `CORRECTION` المباشرة، لكن آلية التصحيح المعتمدة نفسها ليست جزءًا من Sprint 20 ولا يجوز اختراعها هنا. |
| Low | لا توجد شاشة/API مستقلة لـ Audit Log أو إدارة المستخدمين ضمن النطاق الحالي، رغم وجود policy helper لسجل التدقيق. |

## Verification Evidence

```text
python manage.py migrate: audit.0002 applied successfully
python manage.py check: OK
python manage.py check --deploy: 0 issues with generated production secret
pytest -q: 24 passed
python -m compileall -q api apps config: OK
git diff --check: OK
```

## Final Decision

**SPRINT 20: 🟡 PARTIAL**

السبب: متطلبات الأمان والعزل والصلاحيات الموجودة فعليًا في النظام تم تنفيذها واختبارها، لكن المشروع لا يحتوي أصلًا على workflow مستقل مكتمل لـ stock adjustment/reversal أو شاشة/API مستقلة لـ Audit Log/User Management. إضافة تلك workflows ستغير نطاق Business Logic ولا ينبغي اختراعها ضمن هذه الجولة.

### Recommended Next Step

**Sprint 21 فقط**: تحديد وتنفيذ workflow موثق للتصحيح/العكس وسجل التدقيق/إدارة المستخدمين، بعد اعتماد قواعده المحاسبية والصلاحيات المطلوبة. لا يبدأ تلقائيًا.
