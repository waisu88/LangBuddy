from django.shortcuts import render   


def repeat_view(request):
    return render(request, 'langbuddy_repeat.html')


def translate_view(request):
    return render(request, 'langbuddy_translate.html')


def choose_categories_view(request):
    return render(request, 'choose_categories.html')


def main_view(request):
    return render(request, 'main_menu.html')


def progress_view(request):
    return render(request, 'progress_view.html')

