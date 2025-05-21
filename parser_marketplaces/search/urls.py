# urls.py

from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

app_name = 'search'

urlpatterns = [
    path('search/', views.search_view, name='search_page'),
    path('search/<str:product_name>/', views.search_view, name='product_search'),
]

