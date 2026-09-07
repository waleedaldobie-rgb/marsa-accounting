# نظام مرسى — Django Scaffold

هذا المجلد يحتوي على الهيكل الأساسي لمشروع Django مستقل لنظام محاسبة ومخزون محلات الأسماك.

## التشغيل المحلي

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

افتح `http://127.0.0.1:8000/health/` للتحقق من حالة الخدمة، و`/admin/` للوحة الإدارة.

يستخدم المشروع PostgreSQL عند وضع `DATABASE_URL` بصيغة PostgreSQL، ويستخدم SQLite محلياً كخيار تطوير احتياطي فقط. لا تضع الأسرار داخل Git.

## النطاق الحالي

تم تجهيز المشروع، المستخدم المخصص، الأدوار الأولية، الفروع، والمستودعات. الوحدات المحاسبية والمخزنية ستنفذ في مراحل Sprint التالية.
