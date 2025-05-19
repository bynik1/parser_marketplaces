from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('search/<str:product_name>/', views.product_search, name='product_search'),
    path('search/', views.search_page, name='search_page'),
]