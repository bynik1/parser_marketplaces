from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from django.template.loader import render_to_string


menu = [{'title': "О сайте", 'url_name': 'about'},
        {'title': "История", 'url_name': 'history'},
        {'title': "Войти", 'url_name': 'login'}
]

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

def login(request):
    return render(request, 'main/index.html')
