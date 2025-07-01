from django.urls import path
from . import views


app_name = 'api'


urlpatterns = [
    # path('categories/', ),
    path('parse/', views.ProductParseView.as_view(), name='parse'),
    path('category-path/', views.CategoriesPathView.as_view(), name='categories-path'),
    path('products/', views.ProductListView.as_view(), name='products'),
    path('charts/', views.ChartDataView.as_view(), name='charts'),
]
