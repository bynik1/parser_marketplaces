from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
import sys
from search.models import SearchQuery, Product
from users.models import User
from wb_api import ProductManager  # ✅
from django.shortcuts import redirect   
from .utils import menu
from django.contrib.auth.decorators import login_required # ✅
import logging


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()]
)

logger = logging.getLogger(__name__)


data_db = [
    {'id': 1, 'title': 'Анджелина Джоли', 'content': 'Биография Анджелины Джоли', 'is_published': True},
    {'id': 2, 'title': 'Марго Робби', 'content': 'Биография Марго Робби', 'is_published': False},
    {'id': 3, 'title': 'Джулия Робертс', 'content': 'Биография Джулия Робертс', 'is_published': True},
]

def index(request):
    data = {
        'title': 'Главная страница',
        'menu': menu,
    }

    return render(request, 'main/index.html', context=data)

def page_not_found(request, exception):
    return HttpResponseNotFound('Страница не найдена')

def about(request):
    return render(request, 'main/about.html', {'title': 'О сайте', 'menu': menu})

@login_required # ✅
def history(request):
    user_queries = SearchQuery.objects.filter(user=request.user)
    for query in user_queries:
        logger.info(f"{query}")
    data = {
        'title': 'История поиска',
        'requests': user_queries,
        'menu': menu
    }
    return render(request, 'main/history.html', context=data)

def history_detail(request, history_id):
    search_query = get_object_or_404(SearchQuery, id=history_id, user=request.user)
    
    # Получаем товары, связанные с этим запросом
    products = Product.objects.filter(searchquery=search_query)
    
    return render(request, 'main/history_detail.html', {'products': products})