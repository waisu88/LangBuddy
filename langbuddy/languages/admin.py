from django.contrib import admin

# Register your models here.
from .models import Language, Category, Sentence, Translation

admin.site.register((Language, Category, Sentence, Translation, ))