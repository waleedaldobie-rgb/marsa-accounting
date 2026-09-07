from django.urls import path
from . import views
from . import waste_views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_overview, name='overview'),
    path('waste/', waste_views.waste_list, name='waste_list'),
    path('waste/new/', waste_views.waste_create, name='waste_create'),
    path('waste/<int:pk>/', waste_views.waste_detail, name='waste_detail'),
    path('waste/<int:pk>/approve/', waste_views.waste_approve, name='waste_approve'),
    path('waste/<int:pk>/cancel/', waste_views.waste_cancel, name='waste_cancel'),
]
