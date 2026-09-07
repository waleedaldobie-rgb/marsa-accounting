from django.urls import path
from . import views
app_name='delivery'
urlpatterns=[
 path('', views.delivery_list, name='list'),
 path('sale/<int:sale_id>/new/', views.delivery_create, name='create'),
 path('<int:pk>/', views.delivery_detail, name='detail'),
 path('<int:pk>/status/<str:status>/', views.delivery_status, name='status'),
 path('<int:pk>/settle/', views.delivery_settle, name='settle'),
]
