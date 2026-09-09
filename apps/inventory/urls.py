from django.urls import path
from . import views
from . import waste_views
from . import adjustment_views

app_name = 'inventory'

urlpatterns = [
    path('', views.inventory_overview, name='overview'),
    path('adjustments/', adjustment_views.adjustment_list, name='adjustment_list'),
    path('adjustments/new/', adjustment_views.adjustment_create, name='adjustment_create'),
    path('adjustments/<int:pk>/', adjustment_views.adjustment_detail, name='adjustment_detail'),
    path('adjustments/<int:pk>/approve/', adjustment_views.adjustment_approve, name='adjustment_approve'),
    path('adjustments/<int:pk>/cancel/', adjustment_views.adjustment_cancel, name='adjustment_cancel'),
    path('waste/', waste_views.waste_list, name='waste_list'),
    path('waste/new/', waste_views.waste_create, name='waste_create'),
    path('waste/<int:pk>/', waste_views.waste_detail, name='waste_detail'),
    path('waste/<int:pk>/approve/', waste_views.waste_approve, name='waste_approve'),
    path('waste/<int:pk>/cancel/', waste_views.waste_cancel, name='waste_cancel'),
]
