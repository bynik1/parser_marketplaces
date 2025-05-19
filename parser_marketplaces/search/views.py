from django.shortcuts import render
from django.http import HttpResponse
from wb_api import ProductManager
from .models import Product_WB, Product_Ozon
from main.utils import menu
from django.contrib.auth.decorators import login_required

import logging
logger = logging.getLogger(__name__)

def search_page(request):
    product_name = None
    if request.method == 'POST':
        product_name = request.POST.get('inputText')
        logger.debug(f"Searching for: {product_name}")
        if product_name:
            from django.shortcuts import redirect
            from django.urls import reverse
            return redirect(reverse('search:product_search', kwargs={'product_name': product_name}))

    data = {
        'title': 'Главная страница',
        'menu': menu,
        'value': product_name,
    }
    return render(request, 'search/search_page.html', context=data)

@login_required
def product_search(request, product_name):
    logger.info(f"Выполняется поиск и сохранение для товара: {product_name}")
    wb_results = ProductManager().search_and_display(product_name)  # Возвращает список объектов Product

    if wb_results:
        for product_object in wb_results:
            product, created = Product_WB.objects.update_or_create(
                product_id=product_object.product_id,
                defaults={
                    'name': product_object.name,
                    'brand': product_object.brand,
                    'review_rating': product_object.review_rating,
                    'feedbacks': product_object.feedbacks,
                    'color': product_object.color,
                    'price_product': product_object.price_product,
                    'price_basic': product_object.price_basic,
                    'supplier_id': product_object.supplier_id,
                    'supplier_rating': product_object.supplier_rating,
                    'pics': product_object.pics,
                    'first_image_path': product_object.first_image_path,
                }
            )
    display_results = Product_WB.objects.filter(name__icontains=product_name)

    data = {
        'title': f'Результаты поиска для "{product_name}"',
        'product_name': product_name,
        'wb_results': display_results,
        'menu': menu,
    }
    return render(request, 'search/product_results.html', context=data)
