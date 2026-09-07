from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("reports/sales/", views.sales_report, name="sales"),
    path("reports/inventory/", views.inventory_report, name="inventory"),
    path("reports/waste/", views.waste_report, name="waste"),
    path("reports/ledger/", views.financial_ledger, name="financial_ledger"),
    path("reports/sales/export.csv", views.export_sales_csv, name="sales_export"),
    path("health/", views.health, name="health"),
]
