from django.urls import path
from . import views
app_name = 'closing'
urlpatterns = [
    path('', views.closing_list, name='list'),
    path('shift/<int:shift_id>/new/', views.closing_create, name='create'),
    path('<int:pk>/', views.closing_detail, name='detail'),
    path('<int:pk>/approve/', views.closing_approve, name='approve'),
    path('<int:pk>/reject/', views.closing_reject, name='reject'),
]
