from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string
import sys
from wb_api import ProductManager  # ✅
from ozon_selenium import OzonParser  # ✅
from django.shortcuts import redirect   
from .models import Product_WB


menu = [{'title': "О сайте", 'url_name': 'about'},
        {'title': "История", 'url_name': 'history'},
        # {'title': "Войти", 'url_name': 'login'}
]

data_db = [
    {'id': 1, 'title': 'Анджелина Джоли', 'content': 'Биография Анджелины Джоли', 'is_published': True},
    {'id': 2, 'title': 'Марго Робби', 'content': 'Биография Марго Робби', 'is_published': False},
    {'id': 3, 'title': 'Джулия Робертс', 'content': 'Биография Джулия Робертс', 'is_published': True},
]

def index(request):
    product_name = None
    if request.method == 'POST':
        product_name = request.POST.get('inputText')
        print(f"Ввели: {product_name}", file=sys.stdout, flush=True)
        # if product_name:
        #     ProductManager().search_and_display(product_name)
        #     # OzonParser(input_value).run()
        #     # return redirect(f'/results/?query={input_value}')
        #     return redirect('product_search', product_name=product_name)

    data = {
        'title': 'Главная страница',
        'menu': menu,
        'value': product_name,  # передаём введённое значение (если есть)
    }

    return render(request, 'main/index.html', context=data)


def product_search(request, product_name):
    print(f"Выполняется поиск и сохранение для товара: {product_name}", file=sys.stdout, flush=True)
    wb_results = ProductManager().search_and_display(product_name) # Возвращает список объектов Product

    if wb_results:
        for product_object in wb_results:
            # Создаем и сохраняем объект модели Product_WB
            # Используем атрибуты объекта Product, возвращаемого search_and_display
            try:
                Product_WB.objects.create(
                    product_id=product_object.product_id,
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
                    first_image_path=product_object.first_image_path,
                    # created_at заполняется автоматически
                )
            except Exception as e:
                print(f"Ошибка при сохранении объекта Product_WB: {e}", file=sys.stdout, flush=True)
                # Обработайте ошибку сохранения, например, если product_id уже существует (UniqueViolation)
                pass # Или добавьте более детальную обработку

    # Всегда извлекаем все результаты для данного товара из базы данных для отображения
    display_results = Product_WB.objects.filter(name__icontains=product_name)

    data = {
        'title': f'Результаты поиска для "{product_name}"',
        'product_name': product_name,
        'wb_results': display_results, # Передаем результаты из базы
        'menu': menu,
    }

    return render(request, 'main/product_results.html', context=data) # Используем новый шаблон


def page_not_found(request, exception):
    return HttpResponseNotFound('Страница не найдена')


def search(request):
    return HttpResponse("Cтраница для поиска")


def about(request):
    return render(request, 'main/about.html', {'title': 'О сайте', 'menu': menu})


def history(request):
    data = {
        'title': 'История поиска',
        'requests': data_db,
        'menu': menu
    }
    return render(request, 'main/history.html', context=data)
    # return HttpResponse(f"Запрос номер: {request_id}",)

def show_request(request, request_id):
    return HttpResponse(f"Отображение статьи с id = {request_id}")