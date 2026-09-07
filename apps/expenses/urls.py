from django.urls import path
from . import views
app_name = 'expenses'
urlpatterns = [
    path('', views.expense_list, name='list'),
    path('new/', views.expense_create, name='create'),
    path('<int:pk>/', views.expense_detail, name='detail'),
    path('<int:pk>/approve/', views.expense_approve, name='approve'),
    path('<int:pk>/cancel/', views.expense_cancel, name='cancel'),
]
