from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from .forms import SearchForm
from . import search_handler
from django.contrib.auth.forms import UserCreationForm
import logging
from .models import Product, ProductDetails, Supplier, QueryRecord

def home(request):
    if request.user.is_authenticated:
        return redirect('search')  # Автоматический переход
    return render(request, 'search_app/home.html')


@login_required
def search(request):

    results = []
    sort_options = [
        {"value": "priceup", "label": "По возрастанию цены"},
        {"value": "pricedown", "label": "По убыванию цены"},
        {"value": "popular", "label": "По популярности"},
        {"value": "rating", "label": "По рейтингу"},
        {"value": "new", "label": "По новинкам"},
        {"value": "benefit", "label": "Сначала выгодные"},
    ]
    selected_sort = "priceup"  # Значение по умолчанию

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            query = form.cleaned_data['query']
            limit = form.cleaned_data['limit']
            selected_sort = request.POST.get('sort', 'priceup')

            # Обновление результатов поиска
            results = search_handler.perform_search(query, limit, sort=selected_sort)
            for result in results:
                result['image'] = f"media/image/{result['product_id']}/1.jpg"

            # Сохранение данных в базу данных
            for result in results:
                product, created = Product.objects.get_or_create(
                    query_id=result['query_id'],
                    product_id=result['product_id'],
                    defaults={
                        'name': result['name'],
                        'sizes_price_product': result['sizesPriceProduct'],
                    }
                )
                
                # Сохранение деталей продукта
                ProductDetails.objects.update_or_create(
                    product=product,
                    query_id=result['query_id'],
                    defaults={
                        'brand': result['brand'],
                        'color': result['color'],
                        'sizes_price_basic': result.get('sizesPriceBasic'),
                        'review_rating': result['reviewRating'],
                        'feedbacks': result['feedbacks'],
                        'image': f"media/image/{result['product_id']}/1.jpg",
                    }
                )

                # Сохранение информации о поставщике
                Supplier.objects.update_or_create(
                    product=product,
                    query_id=result['query_id'],
                    defaults={
                        'supplier_id': result.get('supplierId'),
                        'supplier': result.get('supplier'),
                        'supplier_rating': result.get('supplierRating'),
                    }
                )

    else:
        form = SearchForm()

    return render(request, 'search_app/search.html', {
        'form': form,
        'results': results,
        'sort_options': sort_options,
        'selected_sort': selected_sort
    })

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})
