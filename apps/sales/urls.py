from django.urls import path
from . import views
from . import return_views

app_name = "sales"
urlpatterns = [
    path("", views.sale_list, name="list"),
    path("pos/", views.pos, name="pos"),
    path("<int:pk>/", views.sale_detail, name="detail"),
    path("<int:pk>/issue/", views.sale_issue, name="issue"),
    path("shifts/", views.shift_list, name="shifts"),
    path("shifts/open/", views.shift_open, name="shift_open"),
    path("returns/", return_views.return_list, name="returns"),
    path("<int:sale_id>/return/new/", return_views.return_create, name="return_create"),
    path("returns/<int:pk>/", return_views.return_detail, name="return_detail"),
    path("returns/<int:pk>/approve/", return_views.return_approve, name="return_approve"),
    path("returns/<int:pk>/cancel/", return_views.return_cancel, name="return_cancel"),
]
