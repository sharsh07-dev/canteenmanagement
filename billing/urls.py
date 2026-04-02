from django.urls import path
from . import views

urlpatterns = [
    path('pos/', views.pos, name='pos'),
    path('create-order/', views.create_order, name='create_order'),
    path('receipt/<int:order_id>/', views.receipt, name='receipt'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('api/items/', views.get_items_api, name='get_items_api'),
]
