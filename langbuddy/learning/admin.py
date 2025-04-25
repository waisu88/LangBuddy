from django.contrib import admin
from .models import UserProgress, UserCategoryProgress, UserCategoryPreference, UserSentenceProgress

# Register your models here.
admin.site.register((UserProgress, UserCategoryProgress, UserCategoryPreference, UserSentenceProgress, ))