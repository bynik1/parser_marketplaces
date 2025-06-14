from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.conf import settings
import os
from .forms import SearchForm
from .models import Product, SearchQuery, SORT_VALUE_CHOICES, SORT_PARAM_MAPPING
from wb_api import ProductManager as WBProductManager
from yandex_api import ProductManager as YandexProductManager
from mm_api import ProductManager as MMProductParser
import logging
import itertools
import json

# Константа с вариантами сортировки
SORT_OPTIONS = [
    {"value": value, "label": label} for value, label in SORT_VALUE_CHOICES
]
logger = logging.getLogger(__name__)

@login_required
def search_view(request, product_name=None):
    # Определяем названия маркетплейсов как строки
    marketplace_wb_name = "Wildberries"
    marketplace_yandex_name = "Яндекс.Маркет"
    marketplace_mm_name = "Мегамаркет"

    # Определяем фильтры один раз
    sort_options = SORT_OPTIONS

    # Получаем значение из GET-параметра
    sort_value = request.GET.get('sort', 'priceup')
    logger.info(f"Фильтр сортировки: {sort_value}")

    if product_name:
        query = product_name
        # Получаем выбранные маркетплейсы из GET-параметров
        selected_marketplaces = request.GET.getlist('marketplaces', [marketplace_wb_name, marketplace_yandex_name, marketplace_mm_name])
    elif request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            sort_value = request.POST.get('sort', 'priceup')
            selected_marketplaces = request.POST.getlist('marketplaces', [marketplace_wb_name, marketplace_yandex_name, marketplace_mm_name])
            if not selected_marketplaces:
                selected_marketplaces = [marketplace_wb_name, marketplace_yandex_name, marketplace_mm_name]
            return redirect(f"{reverse('search:product_search', kwargs={'product_name': query})}?sort={sort_value}&{'&'.join(f'marketplaces={m}' for m in selected_marketplaces)}")
    else:
        form = SearchForm()
        query = None
        selected_marketplaces = [marketplace_wb_name, marketplace_yandex_name, marketplace_mm_name]

    if query:
        wb_sort = SORT_PARAM_MAPPING.get(sort_value, {}).get("wb", sort_value)
        yandex_sort = SORT_PARAM_MAPPING.get(sort_value, {}).get("yandex", "dpop")
        mm_sort = int(SORT_PARAM_MAPPING.get(sort_value, {}).get("mm", "0"))

        wb_results = []
        yandex_results = []
        mm_results = []

        # Поиск на выбранных маркетплейсах
        if marketplace_wb_name in selected_marketplaces:
            wb_results = WBProductManager().search_and_display(query, wb_sort)
        if marketplace_yandex_name in selected_marketplaces:
            yandex_results = YandexProductManager().search_and_display(query, yandex_sort)
        if marketplace_mm_name in selected_marketplaces:
            mm_parser = MMProductParser(
                product_name=query,
                cookie_file_path=os.path.join(settings.BASE_DIR, "cookies.json"),
                log_level="INFO",
                max_pages=1,
                sorting=mm_sort,
            )
            mm_parser.parse()
            mm_results = mm_parser.parsed_offers

        # Сохраняем запрос в SearchQuery
        search_query = SearchQuery.objects.create(
            user=request.user,
            query_text=query,
            sort_value=sort_value,
            marketplace_names=json.dumps(selected_marketplaces)
        )

        wb_objects = []
        yandex_objects = []
        mm_objects = []

        # Обработка результатов Wildberries
        if wb_results:
            for product in wb_results:
                try:
                    if not hasattr(product, 'product_id') or not hasattr(product, 'name'):
                        logger.info(f"Пропущен товар с недостаточными данными: {vars(product)}")
                        continue
                    wb_image_path = f"image/wb/{product.product_id}/1.jpg"
                    full_image_path = os.path.join(settings.MEDIA_ROOT, wb_image_path)
                    first_image_path = f"/media/{wb_image_path}" if os.path.exists(full_image_path) else None
                    obj = Product.objects.create(
                        marketplace_name=marketplace_wb_name,
                        searchquery=search_query,
                        product_id=product.product_id,
                        name=product.name or "Без названия",
                        brand=product.brand,
                        review_rating=product.review_rating,
                        feedbacks=product.feedbacks,
                        color=product.color,
                        price_product=product.price_product,
                        price_basic=product.price_basic,
                        supplier_id=product.supplier_id,
                        supplier_rating=product.supplier_rating,
                        pics=product.pics or 0,
                        first_image_path=first_image_path
                    )
                    wb_objects.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {getattr(product, 'name', 'Unknown')}: {e}")
                    continue

        # Обработка результатов Яндекс.Маркета
        if yandex_results:
            logger.info("Yandex results count: %s", len(yandex_results))
            for product in yandex_results:
                try:
                    if not hasattr(product, 'product_id') or not hasattr(product, 'name'):
                        logger.warning(f"Пропущен товар с недостаточными данными: {vars(product)}")
                        continue
                    yandex_image_path = f"image/yma/{product.product_id}/1.jpg" if getattr(product, 'image_url', None) else None
                    first_image_path = None
                    if yandex_image_path:
                        full_image_path = os.path.join(settings.MEDIA_ROOT, yandex_image_path)
                        first_image_path = f"/media/{yandex_image_path}" if os.path.exists(full_image_path) else None
                    obj = Product.objects.create(
                        marketplace_name=marketplace_yandex_name,
                        searchquery=search_query,
                        product_id=int(product.product_id) if product.product_id else 0,
                        name=product.name or "Без названия",
                        brand=product.brand,
                        review_rating=product.rating,
                        feedbacks=product.reviews_count,
                        color=None,
                        price_product=product.price,
                        price_basic=product.original_price,
                        supplier_id=None,
                        supplier_rating=None,
                        pics=1 if getattr(product, 'image_url', None) else 0,
                        first_image_path=first_image_path,
                        url=product.url,
                        delivery_date=product.delivery_date,
                        duty=product.duty
                    )
                    yandex_objects.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {getattr(product, 'name', 'Unknown')}: {e}")
                    continue

        # Обработка результатов Мегамаркета
        if mm_results:
            logger.info("Megamarket results count: %s", len(mm_results))
            for product in mm_results:
                try:
                    if not hasattr(product, 'product_id') or not hasattr(product, 'name'):
                        logger.warning(f"Пропущен товар с недостаточными данными: {vars(product)}")
                        continue
                    mm_image_path = f"image/mm/{product.product_id}/1.jpg" if getattr(product, 'image_url', None) else None
                    first_image_path = None
                    if mm_image_path:
                        full_image_path = os.path.join(settings.MEDIA_ROOT, mm_image_path)
                        first_image_path = f"/media/{mm_image_path}" if os.path.exists(full_image_path) else None
                    obj = Product.objects.create(
                        marketplace_name=marketplace_mm_name,
                        searchquery=search_query,
                        product_id=product.product_id,
                        name=product.name or "Без названия",
                        brand=product.brand,
                        review_rating=product.rating,
                        feedbacks=product.reviews_count,
                        color=None,
                        price_product=product.price,
                        price_basic=product.old_price,
                        supplier_id=product.merchant_id,
                        supplier_rating=product.merchant_rating,
                        pics=1 if getattr(product, 'image_url', None) else 0,
                        first_image_path=first_image_path,
                        url=product.url,
                        delivery_date=product.delivery_date,
                        duty=None
                    )
                    mm_objects.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {getattr(product, 'name', 'Unknown')}: {e}")
                    continue

        # Составляем общий список товаров в зависимости от выбранного фильтра
        if sort_value == "popular":
            display_results = []
            for wb_obj, ym_obj, mm_obj in itertools.zip_longest(wb_objects, yandex_objects, mm_objects):
                if wb_obj:
                    display_results.append(wb_obj)
                if ym_obj:
                    display_results.append(ym_obj)
                if mm_obj:
                    display_results.append(mm_obj)
        else:
            display_results = wb_objects + yandex_objects + mm_objects
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
            'selected_marketplaces': selected_marketplaces,
        }

        return render(request, 'product_results.html', context=data)

    return render(request, 'search/search_form.html', {
        'form': form,
        'sort_options': sort_options,
        'current_sort': sort_value,
        'selected_marketplaces': selected_marketplaces,
    })