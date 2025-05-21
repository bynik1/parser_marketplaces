from django.urls import path
from main import views

urlpatterns = [
    path('', views.index, name='home'),
    path('about/', views.about, name='about'),
    path('history/', views.history, name='history'),
    path('history/<int:history_id>/', views.history_detail, name='search_history_detail'),
]

