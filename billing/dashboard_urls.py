from django.urls import path
from billing import views as billing_views

urlpatterns = [
    path('', billing_views.dashboard, name='dashboard'),
]
