from django.contrib import admin
from django.urls import include, path
from django.contrib.auth import views as auth_views
from .health import health

urlpatterns = [
    path("health/", health, name="health"),
    path("admin/", admin.site.urls),
    path("api/v1/", include("api.urls")),
    path("login/", auth_views.LoginView.as_view(template_name="registration/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("apps.reports.urls")),
    path("catalog/", include("apps.catalog.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("purchases/", include("apps.purchases.urls")),
    path("delivery/", include("apps.delivery.urls")),
    path("expenses/", include("apps.expenses.urls")),
    path("sales/", include("apps.sales.urls")),
    path("closing/", include("apps.closing.urls")),
]
