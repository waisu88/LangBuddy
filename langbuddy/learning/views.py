from django.db import models
from django.db.models import OuterRef, Subquery, IntegerField, Exists, Value as V
from django.db.models.functions import Coalesce
from .models import UserProgress, UserCategoryPreference, UserSentenceProgress
from languages.models import Sentence

def choose_sentence(user, mode="repeat"):
    # 1. Globalny poziom użytkownika
    user_progress = UserProgress.objects.filter(user=user).first()
    level = user_progress.global_level if user_progress else 'B1'

    # 2. Preferowane kategorie użytkownika
    preferred_categories = UserCategoryPreference.objects.filter(
        user=user,
        is_active=True
    ).values_list('category_id', flat=True)

    # 3. Bazowy queryset zdań
    if not preferred_categories:
        base_sentences = Sentence.objects.all()
    else:
        base_sentences = Sentence.objects.filter(
            level=level,
            category_id__in=preferred_categories
        )

    # 4. Wykluczenie opanowanych zdań (is_mastered=True)
    mastered_subquery = UserSentenceProgress.objects.filter(
        user=user,
        sentence=OuterRef('pk'),
        is_mastered=True
    )
    base_sentences = base_sentences.annotate(
        is_mastered=Exists(mastered_subquery)
    ).filter(is_mastered=False)

    # 4b. Dodatkowe filtrowanie dla trybu "translate" → tylko te, które były już powtarzane
    if mode == "translate":
        repeated_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence=OuterRef('pk'),
            repeat_attempts__gt=0
        )
        base_sentences = base_sentences.annotate(
            was_repeated=Exists(repeated_subquery)
        ).filter(was_repeated=True)

    # 5. Annotacja liczby prób
    if mode == "repeat":
        progress_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence=OuterRef('pk')
        ).values('repeat_attempts')[:1]
    elif mode == "translate":
        progress_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence=OuterRef('pk')
        ).values('translate_attempts')[:1]
    else:
        progress_subquery = UserSentenceProgress.objects.none().values('repeat_attempts')

    annotated = base_sentences.annotate(
        attempts=Coalesce(Subquery(progress_subquery), V(0), output_field=IntegerField())
    )

    # 6. Sortowanie i wybór zdania
    sentence = annotated.order_by('attempts', '?').first()
    return sentence



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
from django.conf import settings

from io import BytesIO
from gtts import gTTS


def repeat(request):
    user = request.user
    sentence = choose_sentence(user=user, mode="repeat")

    if not sentence:
        return JsonResponse({'error': 'Brak dostępnych zdań'}, status=404)

    translation = sentence.translations.filter(language__code="hr").first()
    if not translation:
        return JsonResponse({'error': 'Brak tłumaczenia'}, status=404)

    tts = gTTS(text=translation.content, lang="hr")
    tts_io = BytesIO()
    tts.write_to_fp(tts_io)
    tts_io.seek(0)

    audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
    with open(audio_path, "wb") as f:
        f.write(tts_io.read())

    audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")

    return JsonResponse({
        'mode': 'repeat',
        'audio_url': audio_url,
        'sentence': {
            'id': sentence.id,
            'content': sentence.content,
            'level': sentence.level,
            'category': sentence.category.name if sentence.category else None
        }
    })


def translate(request):
    user = request.user
    sentence = choose_sentence(user=user, mode="translate")
    
    if not sentence:
        return JsonResponse({'error': 'Brak dostępnych zdań'}, status=404)

    return JsonResponse({
        "mode": "translate",
        "sentence": {
            "id": sentence.id,
            "content": sentence.content,
            "level": sentence.level,
            "category": sentence.category.name if sentence.category else None
        }
    })


from learning.models import UserProgress
from languages.models import Sentence
# import whisper
from .whisper_model import model as whisper_model



@csrf_exempt
def check_answer(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        # ⬇️ Transkrybujemy audio przez osobną funkcję
        transcription = upload_audio(request)
        # Pobranie trybu nauki i zdania
        sentence_id = request.POST.get('sentence_id')
        if not sentence_id:
            return JsonResponse({'error': 'Brak ID zdania'}, status=400)

        try:
            sentence = Sentence.objects.get(id=sentence_id)
        except Sentence.DoesNotExist:
            return JsonResponse({'error': 'Nie znaleziono zdania'}, status=404)
        
        translation = sentence.translations.filter(language__code="hr").first().content

        score = calculate_similarity(transcription, translation)

        
        mode = request.POST.get('mode')
        update_sentence_progress(user=request.user, sentence=sentence, mode=mode, score=score)

        return JsonResponse({
            'transkrypcja': transcription,
            'sentence': sentence.content,
            'translation': translation,
            'levenshtein_score': score
        })

    return JsonResponse({'error': 'Niepoprawne zapytanie'}, status=400)



WHISPER_AUDIO_DIR = "/tmp/whisper"  # katalog zamontowany w docker-compose

def upload_audio(request):
    audio_file = request.FILES['audio']
    user_id = request.user.id if request.user.is_authenticated else "anon"
    
    # Plik o nazwie zależnej od użytkownika
    file_name = f"audio_{user_id}.wav"
    file_path = os.path.join(WHISPER_AUDIO_DIR, file_name)

    # Zapisujemy plik (nadpisuje poprzedni)
    with open(file_path, 'wb') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)
    transcription = transcribe_audio(file_path)

    try:
        os.remove(file_path)
    except Exception as e:
        print(f"⚠️ Nie udało się usunąć pliku audio: {e}")

    return transcription


def transcribe_audio(file_path):
    result = whisper_model.transcribe(file_path, language="hr")
    transcription = result['text'].strip()
    return transcription


from Levenshtein import distance as levenshtein

def calculate_similarity(transcription, translation):
    distance = levenshtein(transcription, translation)
    score = (1 - distance / max(len(transcription), len(translation))) * 100
    return score

"""Dziająca funkcja"""
# def update_sentence_progress(user, sentence, mode, score):
#     progress, created = UserSentenceProgress.objects.get_or_create(user=user, sentence=sentence)
#     progress.update_progress(similarity_score=score, attempt_type=mode)

#     return Response({
#         "status": "updated",
#         "is_mastered": progress.is_mastered,
#         "accuracy": progress.accuracy()
#     })
"""Nowa, niesprawdzona funkcja"""
def update_sentence_progress(user, sentence, mode, score):
    progress, created = UserSentenceProgress.objects.get_or_create(user=user, sentence=sentence)
    progress.update_progress(similarity_score=score, attempt_type=mode)

    # ⬇️ Nowa część: AKTUALIZACJA postępu kategorii
    category = sentence.category
    language = sentence.language

    # ⬇️ Pobierz lub utwórz postęp kategorii
    category_progress, _ = UserCategoryProgress.objects.get_or_create(
        user=user,
        category=category,
        language=language
    )

    # ⬇️ Zbierz wszystkie postępy użytkownika w tej kategorii i języku
    all_progress = UserSentenceProgress.objects.filter(
        user=user,
        sentence__category=category,
        sentence__language=language
    )

    # ⬇️ Oblicz średni similarity score
    average_similarity = all_progress.aggregate(avg=models.Avg('last_similarity_score'))['avg'] or 0.0

    # ⬇️ Poziomy CEFR
    CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    current_index = CEFR_LEVELS.index(category_progress.level)

    # ⬇️ Reguły zmiany poziomu
    if average_similarity >= 0.8 and current_index < len(CEFR_LEVELS) - 1:
        category_progress.level = CEFR_LEVELS[current_index + 1]
    elif average_similarity < 0.4 and current_index > 0:
        category_progress.level = CEFR_LEVELS[current_index - 1]
    # else: poziom pozostaje bez zmian

    category_progress.save()

    # # ⬇️ AKTUALIZACJA GLOBALNEGO poziomu użytkownika
    # all_category_levels = UserCategoryProgress.objects.filter(user=user)
    # if all_category_levels.exists():
    #     level_indices = [CEFR_LEVELS.index(p.level) for p in all_category_levels]
    #     average_level_index = round(sum(level_indices) / len(level_indices))
    #     global_level = CEFR_LEVELS[average_level_index]

    #     user_progress, _ = UserProgress.objects.get_or_create(user=user, language=language)
    #     user_progress.global_level = global_level
    #     user_progress.save()

    # ⬇️ Zwrotka, jeśli potrzebujesz do API
    return {
        "status": "updated",
        "is_mastered": progress.is_mastered,
        "accuracy": progress.accuracy()
    }




def update_user_progress(user, language, score):
    progress, _ = UserProgress.objects.get_or_create(user=user, language=language)

    progress.attempts += 1
    if score > 80:
        progress.score += 1

    # Zmiana poziomu trudności co 10 poprawnych odpowiedzi
    levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    if progress.score % 10 == 0:
        current_index = levels.index(progress.level)
        if current_index < len(levels) - 1:
            progress.level = levels[current_index + 1]

    progress.save()


"""Widoki dla progresu. Model based Views"""


from rest_framework import generics
from .models import UserProgress, UserCategoryProgress, UserCategoryPreference, UserSentenceProgress
from .serializers import UserCategoryPreferenceSerializer, UserCategoryProgressSerializer, UserProgressSerializer, UserSentenceProgressSerializer

class UserProgressAPIView(generics.ListAPIView):
    serializer_class = UserProgressSerializer
    queryset = UserProgress.objects.all()


class UserCategoryProgressAPIView(generics.ListAPIView):
    serializer_class = UserCategoryProgressSerializer
    queryset = UserCategoryProgress.objects.all()


class UserCategoryPreferenceAPIView(generics.ListAPIView):
    serializer_class = UserCategoryPreferenceSerializer
    queryset = UserCategoryPreference.objects.all()


class UserSentenceProgressAPIView(generics.ListAPIView):
    serializer_class = UserSentenceProgressSerializer
    queryset = UserSentenceProgress.objects.all()

from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserCategoryPreference



@csrf_exempt
@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def user_category_preferences(request):
    user = request.user

    if request.method == 'GET':
        # Zwróć tylko ID aktywnych kategorii użytkownika
        preferences = UserCategoryPreference.objects.filter(user=user, is_active=True)

        selected_categories = [
            {
                "category_id": pref.category.id,
                "category_name": pref.category.name,
                "priority": pref.priority
            }
            for pref in preferences
        ]

        return Response(selected_categories)
    
    if request.method == 'POST':
        print("Start")
        selected_categories = request.data.get('selected_categories', [])
        print(selected_categories)

        # Dezaktywuj wszystkie stare
        UserCategoryPreference.objects.filter(user=user).update(is_active=False)

        # Aktywuj wybrane
        for cat_id in selected_categories:
            pref, created = UserCategoryPreference.objects.get_or_create(user=user, category_id=cat_id)
            pref.is_active = True
            pref.save()

        return Response({"status": "preferences updated"})