from main.utils import menu

def menu_context_processor(request):
    return {'menu': menu}
