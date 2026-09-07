from django.urls import path
from . import views

app_name = "catalog"
urlpatterns = [
    path("products/", views.product_list, name="products"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/", views.product_detail, name="product_detail"),
    path("products/<int:pk>/price/", views.add_price, name="add_price"),
    path("products/import/", views.product_csv_import, name="import"),
    path("products/import/template/", views.product_csv_template, name="import_template"),
    path("suppliers/", views.supplier_list, name="suppliers"),
    path("suppliers/new/", views.supplier_create, name="supplier_create"),
]
