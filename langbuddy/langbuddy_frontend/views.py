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


from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from authorization.models import Profile
from django.contrib.auth import login

def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Tworzymy profil z domyślnymi wartościami
            Profile.objects.get_or_create(user=user)
            login(request, user)
            return redirect('/')  # zmień na swoją nazwę widoku głównego
    else:
        form = UserCreationForm()
    return render(request, 'langbuddy_register.html', {'form': form})

