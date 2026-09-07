from django.db import connection
from django.http import JsonResponse


def health(request):
    status = "ok"
    db = "ok"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception:
        status = "degraded"
        db = "error"
    return JsonResponse({"status": status, "database": db}, status=200 if status == "ok" else 503)
