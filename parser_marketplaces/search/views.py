# views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import SearchForm
from .models import Product, Marketplace, SearchQuery, SORT_VALUE_CHOICES, SORT_PARAM_MAPPING
from wb_api import ProductManager as WBProductManager
from yandex_api import ProductManager as YandexProductManager
import logging

import itertools
# Константа с вариантами сортировки
SORT_OPTIONS = [
    {"value": value, "label": label} for value, label in SORT_VALUE_CHOICES
]
logger = logging.getLogger(__name__)
@login_required
def search_view(request, product_name=None):
    marketplace_wb = get_object_or_404(Marketplace, name="Wildberries")
    marketplace_yandex = get_object_or_404(Marketplace, name="Яндекс.Маркет")

    # Определяем фильтры один раз
    sort_options = SORT_OPTIONS

    # Получаем значение из GET-параметра
    sort_value = request.GET.get('sort', 'priceup')
    logging.info(f"Фильтр сортировки: {sort_value}")
    
    # if sort_value not in [opt['value'] for opt in sort_options]:
    #     sort_value = 'priceup'

    if product_name:
        query = product_name
    elif request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            sort_value = request.POST.get('sort', 'priceup')  # получаем строку
            return redirect(f"{reverse('search:product_search', kwargs={'product_name': query})}?sort={sort_value}")
    else:
        form = SearchForm()
        query = None

    if query:
        wb_sort = SORT_PARAM_MAPPING.get(sort_value, {}).get("wb", sort_value)
        yandex_sort = SORT_PARAM_MAPPING.get(sort_value, {}).get("yandex", "dpop")

        wb_results = WBProductManager().search_and_display(query, wb_sort)
        yandex_results = YandexProductManager().search_and_display(query, yandex_sort)
    

        search_query = SearchQuery.objects.create(
            user=request.user,
            query_text=query,
            sort_value=sort_value,
        )
        search_query.marketplaces.add(marketplace_wb, marketplace_yandex)

        wb_objects = []
        yandex_objects = []

        if wb_results:
            for product in wb_results:
                try:
                    obj = Product.objects.create(
                        marketplace=marketplace_wb,
                        searchquery=search_query,
                        product_id=product.product_id,
                        name=product.name,
                        brand=product.brand,
                        review_rating=product.review_rating,
                        feedbacks=product.feedbacks,
                        color=product.color,
                        price_product=product.price_product,
                        price_basic=product.price_basic,
                        supplier_id=product.supplier_id,
                        supplier_rating=product.supplier_rating,
                        pics=product.pics,
                        first_image_path=f"/media/image/wb/{product.product_id}/1.jpg"
                    )
                    wb_objects.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {product.name}: {e}")
                    
        if yandex_results:
            logger.debug("Yandex results count: %s", len(yandex_results))  # Логирование количества результатов
            for product in yandex_results:
                logger.debug("Processing Yandex product: %s", vars(product))  # Логирование данных
                try:
                    obj = Product.objects.create(
                        marketplace=marketplace_yandex,
                        searchquery=search_query,
                        product_id=int(product.product_id) if product.product_id else 0,
                        name=product.name,
                        brand=product.brand,
                        review_rating=product.rating,
                        feedbacks=product.reviews_count,
                        color=None,
                        price_product=product.price,
                        price_basic=product.original_price,
                        supplier_id=None,
                        supplier_rating=None,
                        pics=1 if product.image_url else 0,
                        first_image_path=f"/media/image/yma/{product.product_id}/1.jpg" if product.image_url else None,
                        url=product.url,
                        delivery_date=product.delivery_date,
                        duty=product.duty
                    )
                    yandex_objects.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {product.name}: {e}")

        
        # Составляем общий список товаров в зависимости от выбранного фильтра
        if sort_value == "popular":
            display_results = []
            for wb_obj, ym_obj in itertools.zip_longest(wb_objects, yandex_objects):
                if wb_obj:
                    display_results.append(wb_obj)
                if ym_obj:
                    display_results.append(ym_obj)
        else:
            display_results = wb_objects + yandex_objects
            if sort_value == "priceup":
                display_results.sort(key=lambda p: (p.price_product is None, p.price_product))
            elif sort_value == "pricedown":
                display_results.sort(key=lambda p: (p.price_product is None, p.price_product if p.price_product is not None else 0), reverse=True)
            elif sort_value == "rate":
                display_results.sort(key=lambda p: (p.review_rating is None, p.review_rating if p.review_rating is not None else 0), reverse=True)
        data = {
            'title': f'Результаты поиска товара "{query}"',
            'products': display_results,
            'sort_label': next((opt['label'] for opt in sort_options if opt['value'] == sort_value), sort_value),
            'back_url': reverse('search:search_page'),
            'back_label': 'Вернуться к поиску',
        }

        return render(request, 'product_results.html', context=data)

    return render(request, 'search/search_form.html', {
        'form': form,
        'sort_options': sort_options,       # ✅ Здесь тоже
        'current_sort': sort_value
    })