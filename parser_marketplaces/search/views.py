from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from wb_api import ProductManager
from .models import Product, Marketplace, SearchQuery
from main.utils import menu
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.urls import reverse

import logging
logger = logging.getLogger(__name__)

def search_page(request):
    product_name = request.GET.get('inputText', '')  # Получаем значение поиска из GET, если оно есть
    
    # Проверяем, был ли запрос через POST (для поиска)
    if request.method == 'POST':
        product_name = request.POST.get('inputText')
        logger.debug(f"Searching for: {product_name}")
        if product_name:
            # При поиске добавляем введенное значение и текущие параметры сортировки в URL
            return redirect(reverse('search:product_search', kwargs={'product_name': product_name}))

    # Отправляем параметры для шаблона
    data = {
        'title': 'Главная страница',
        'menu': menu,
        'value': product_name,  # Введенное значение в поле поиска
    }
    return render(request, 'search/search_page.html', context=data)


@login_required
def product_search(request, product_name):
    logger.info(f"Выполняется поиск и сохранение для товара: {product_name}")
    
    # Получаем или создаем маркетплейс (например, Wildberries)
    marketplace = get_object_or_404(Marketplace, name="Wildberries")
    
    # Получаем сортировку из GET параметров
    try:
        search_sort = int(request.GET.get('sort', 0))
    except (ValueError, TypeError):
        search_sort = 0  # Default to popular sorting
        logger.warning(f"Invalid sort parameter provided: {request.GET.get('sort')}")
    
    # Поиск товаров через внешний менеджер
    wb_results = ProductManager().search_and_display(product_name, search_sort)

    # Создаем новый запрос SearchQuery
    search_query = SearchQuery.objects.create(
        user=request.user,
        query_text=product_name
    )
    search_query.marketplaces.add(marketplace)  # Добавляем маркетплейс к запросу

    # Обработка результатов поиска товаров
    if wb_results:
        for product_object in wb_results:
# Создаем новый товар для каждого найденного товара
            try:
                Product.objects.create(
                    product_id=product_object.product_id,
                    marketplace=marketplace,
                    searchquery=search_query,  # Связываем с запросом
                    name=product_object.name,
                    brand=product_object.brand,
                    review_rating=product_object.review_rating,
                    feedbacks=product_object.feedbacks,
                    color=product_object.color,
                    price_product=product_object.price_product,
                    price_basic=product_object.price_basic,
                    supplier_id=product_object.supplier_id,
                    supplier_rating=product_object.supplier_rating,
                    pics=product_object.pics,
                    first_image_path=getattr(product_object, 'first_image_path', None),
                )
                logger.info(f"Товар добавлен: {product_object.name}")
            except Exception as e:
                logger.error(f"Ошибка при добавлении товара {product_object.name}: {e}")

    # Получаем все товары для отображения
    display_results = Product.objects.filter(searchquery=search_query)

    data = {
        'title': f'Результаты поиска для "{product_name}" на {marketplace.name}',
        'product_name': product_name,
        'marketplace': marketplace,
        'wb_results': display_results,
        'menu': menu,
    }

    # Отправляем результаты на страницу
    return render(request, 'search/product_results.html', context=data)


