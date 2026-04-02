from django.urls import path
from . import views

urlpatterns = [
    path('sales/', views.sales_report, name='sales_report'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('inventory/', views.inventory_report, name='inventory_report'),
]
