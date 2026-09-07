# مَرسى — Fish Shop ERP / POS

نظام Django مستقل لإدارة المشتريات والمخزون والمبيعات والحسابات لفروع محلات الأسماك.

## الحالة الحالية
**Foundation / Sprint 1 + domain skeleton**. تم إنشاء المشروع من الصفر ووضع النماذج الأساسية والخدمات الجوهرية ووثائق الاستمرارية. لم يتم اعتبار النظام مكتملًا بعد؛ راجع `PROJECT_STATE.md` قبل تنفيذ أي مرحلة لاحقة.

## التشغيل
1. انسخ `.env.example` إلى `.env`.
2. شغّل PostgreSQL عبر `docker compose up -d db`.
3. ثبّت المتطلبات: `pip install -r requirements.txt`.
4. نفّذ `python manage.py makemigrations` ثم `python manage.py migrate`.
5. أنشئ مديرًا: `python manage.py createsuperuser`.
6. شغّل: `python manage.py runserver`.
7. افحص `http://127.0.0.1:8000/health/`.

## قواعد لا تكسرها
- PostgreSQL هو قاعدة البيانات المعتمدة.
- `StockMovement` هو دفتر الحركة الرسمي؛ `StockBalance` رصيد مشتق سريع.
- لا تعديل مباشر لرصيد المخزون.
- كل عملية مخزون حساسة يجب أن تكون ذرية ومقفلة عند التزامن.
- البيع يخرج الوزن الخام من المخزون، بينما قيمة الفاتورة تحسب من الوزن المنظف.
- التكلفة تستخدم Weighted Average Cost وتُحفظ وقت الحركة/البيع.
- فرق التنظيف لا يعتبر هالكًا تلقائيًا.
- المستندات المعتمدة لا تحذف؛ تستخدم الإلغاء/العكس/التصحيح مع سبب وسجل تدقيق.
- أي تعديل في قواعد الوزن أو التكلفة أو الإغلاق المالي يحتاج قرارًا موثقًا.

## البنية
`accounts` المستخدمون والأدوار — `branches` الفروع والمواقع — `catalog` المنتجات والموردون والأسعار — `inventory` محرك المخزون — `purchases` المشتريات — `transfers` التحويلات — `sales` الورديات والمبيعات والمدفوعات — `processing` الوزن الخام/المنظف — `delivery` تطبيقات التوصيل والتسويات — `expenses` المصروفات — `closing` إغلاق الورديات — `reports` التقارير — `audit` التدقيق.

## الوثيقة المرجعية
اقرأ `PROJECT_STATE.md` و `ARCHITECTURE.md` قبل أي تغيير كبير. عند الانتقال إلى محرر/وكيل آخر، أعطه نص `HANDOFF.md` أو اطلب منه قراءة هذه الملفات أولًا.


## Runtime bootstrap
بعد تثبيت المتطلبات وتشغيل PostgreSQL، شغّل:

`python scripts/bootstrap_runtime.py`

سيقوم بالفحص ثم `makemigrations` ثم `migrate` ثم الاختبارات. لا تُعتبر migrations أو اختبارات PostgreSQL مكتملة قبل تنفيذها فعليًا.
