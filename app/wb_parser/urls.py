from django.urls import path
from . import views


app_name = 'wb'


urlpatterns = [
    path('', views.main_view, name='main'),
    path('categories/', views.categories_view, name='categories'),
    path('items/', views.items_view, name='items'),
]
