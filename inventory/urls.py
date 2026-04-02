from django.urls import path
from . import views

urlpatterns = [
    path('items/', views.item_list, name='item_list'),
    path('items/create/', views.item_create, name='item_create'),
    path('items/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('items/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    path('items/<int:item_id>/adjust/', views.stock_adjust, name='stock_adjust'),
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:cat_id>/edit/', views.category_edit, name='category_edit'),
    path('categories/<int:cat_id>/delete/', views.category_delete, name='category_delete'),
    path('movements/', views.movement_history, name='movement_history'),
]
