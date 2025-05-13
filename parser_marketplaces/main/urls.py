from django.urls import path
from main import views

urlpatterns = [
    path('', views.index, name='home'),
    path('login/', views.login, name='login'),
    # path('search/', views.search, name='search'),
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('history/<int:request_id>/', views.show_request, name='history_id'),
    path('search/<str:product_name>/', views.product_search, name='product_search'),
]
