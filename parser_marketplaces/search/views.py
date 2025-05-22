# views.py

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .forms import SearchForm
from .models import Product, Marketplace, SearchQuery
from wb_api import ProductManager
import logging

logger = logging.getLogger(__name__)
@login_required
def search_view(request, product_name=None):
    marketplace = get_object_or_404(Marketplace, name="Wildberries")

    # Определяем фильтры один раз
    sort_options = [
        {"value": "popular", "label": "По популярности"},
        {"value": "rate", "label": "По рейтингу"},
        {"value": "priceup", "label": "Сначала дешёвые"},
        {"value": "pricedown", "label": "Сначала дорогие"}
    ]

    # Получаем значение из GET-параметра
    sort_value = request.GET.get('sort', 'priceup')
    
    if sort_value not in [opt['value'] for opt in sort_options]:
        sort_value = 'priceup'

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
        wb_results = ProductManager().search_and_display(query, sort_value)

        search_query = SearchQuery.objects.create(user=request.user, query_text=query)
        search_query.marketplaces.add(marketplace)

        display_results = []

        if wb_results:
            for product in wb_results:
                try:
                    obj = Product.objects.create(
                        marketplace=marketplace,
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
                        first_image_path=f"media/image/{product.product_id}/1.jpg"
                    )
                    display_results.append(obj)
                except Exception as e:
                    logger.error(f"Ошибка при сохранении товара {product.name}: {e}")

        data = {
            'title': f'Результаты поиска товара "{query}"',
            'products': display_results,
            'back_url': reverse('search:search_page'),
            'back_label': 'Вернуться к поиску',
        }

        return render(request, 'product_results.html', context=data)

    return render(request, 'search/search_form.html', {
        'form': form,
        'sort_options': sort_options,       # ✅ Здесь тоже
        'current_sort': sort_value
    })