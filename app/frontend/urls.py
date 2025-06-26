from django.urls import path
from . import views


app_name = 'frontend'


urlpatterns = [
    path('', views.main_view, name='main'),
    path('products/', views.products_view, name='products'),
]
