from django.urls import path
from . import views
app_name='purchases'
urlpatterns=[
 path('',views.purchase_list,name='list'), path('new/',views.purchase_create,name='create'), path('<int:pk>/',views.purchase_detail,name='detail'), path('<int:pk>/items/add/',views.purchase_add_item,name='add_item'), path('<int:pk>/approve/',views.purchase_approve,name='approve'), path('<int:pk>/cancel/',views.purchase_cancel,name='cancel'),
 path('returns/',views.return_list,name='returns'), path('returns/new/',views.return_create,name='return_create'), path('returns/<int:pk>/',views.return_detail,name='return_detail'), path('returns/<int:pk>/items/add/',views.return_add_item,name='return_add_item'), path('returns/<int:pk>/approve/',views.return_approve,name='return_approve'),
]
