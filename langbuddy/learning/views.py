from django.db import models
from django.db.models import OuterRef, Subquery, IntegerField, Exists, Value as V, Q, Min
from django.db.models.functions import Coalesce
from .models import UserProgress, UserCategoryPreference, UserSentenceProgress
from languages.models import Sentence


def choose_sentence(user, mode="repeat"):
    # 1. Globalny poziom użytkownika
    user_progress = UserProgress.objects.filter(user=user).first()
    level = user.profile.target_language_level
    # level = user_progress.global_level if user_progress else 'B1'
    
    # 2. Preferowane kategorie użytkownika
    preferred_categories = UserCategoryPreference.objects.filter(
        user=user,
        is_active=True
    ).values_list('category_id', flat=True)
    # 2b. Mapowanie kategorii na poziomy z UserCategoryProgress
    # Dla każdej preferowanej kategorii próbujemy pobrać poziom z UserCategoryProgress,
    # a jeśli nie istnieje – używamy globalnego poziomu użytkownika
    user_category_progress = {
        ucp.category_id: ucp.level
        for ucp in UserCategoryProgress.objects.filter(user=user, category_id__in=preferred_categories)
    }

    category_level_map = {
        cat_id: user_category_progress.get(cat_id, level)  # fallback do globalnego poziomu
        for cat_id in preferred_categories
    }

    # 3. Budowa querysetu bazowego
    if not category_level_map:
        # fallback do globalnego poziomu
        base_sentences = Sentence.objects.filter(level=level)
    else:
        category_filters = Q()
        for cat_id, lvl in category_level_map.items():
            category_filters |= Q(category_id=cat_id, level=lvl)
        base_sentences = Sentence.objects.filter(category_filters)
    # 4. Wykluczenie opanowanych zdań (is_mastered=True)
    # mastered_subquery = UserSentenceProgress.objects.filter(
    #     user=user,
    #     sentence_id=OuterRef('pk'),
    #     is_mastered_translate=True
    # )
    # base_sentences = base_sentences.annotate(
    #     is_mastered=Exists(mastered_subquery)
    # ).filter(is_mastered=False)

    # 4b. W trybie "translate" tylko zdania opanowane w repeat
    if mode == "translate":
        repeated_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence_id=OuterRef('pk'),
            correct_attempts_repeat__gte=1
        )
        # Przynajmniej raz dobrze powtórzone
        base_sentences = base_sentences.annotate(
            was_repeated_once=Exists(repeated_subquery)
        ).filter(was_repeated_once=True)

    # 4c Wyklucz zdania opanowane (dla konkretnego trybu)
    if mode == "repeat":
        filter_mastered = UserSentenceProgress.objects.filter(
            user=user,
            sentence_id=OuterRef('pk'),
            is_mastered_repeat=True
        )
    elif mode == "translate":
        filter_mastered = UserSentenceProgress.objects.filter(
            user=user,
            sentence_id=OuterRef('pk'),
            is_mastered_translate=True
        )

    base_sentences = base_sentences.annotate(
        is_mastered=Exists(filter_mastered)
    ).filter(is_mastered=False)


    # 5. Annotacja liczby prób


    if mode == "repeat":
        progress_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence_id=OuterRef('pk')
        ).values('repeat_attempts')[:1]
    elif mode == "translate":
        progress_subquery = UserSentenceProgress.objects.filter(
            user=user,
            sentence_id=OuterRef('pk')
        ).values('translate_attempts')[:1]
    else:
        progress_subquery = UserSentenceProgress.objects.none().values('repeat_attempts')

    annotated = base_sentences.annotate(
        attempts=Coalesce(Subquery(progress_subquery), V(0), output_field=IntegerField())
    )

    # 6. Sortowanie i wybór zdania
    # Dla poniższego podejscia zauwazyłem brak losowości pomiędzy kategoriami, próbuję sugestii chatuGPT
    sentence = annotated.order_by('attempts', '?').first() 
    # min_attempts = annotated.aggregate(min_attempts=Min('attempts'))['min_attempts']
    # least_attempted = annotated.filter(attempts=min_attempts)
    # sentence = least_attempted.order_by('?').first()
    return sentence



from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
from django.conf import settings

from io import BytesIO
from gtts import gTTS

from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator

@login_required
def repeat(request):
    user = request.user
    sentence = choose_sentence(user=user, mode="repeat")
    if not sentence:
        return JsonResponse({'error': 'Brak dostępnych zdań'}, status=404)
    lang = user.profile.target_language
    if lang == "pl":
        lang == user.profile.native_language
        translation = sentence
    else:
        translation = sentence.translations.filter(language__code=lang).first()
    
    if not translation:
        return JsonResponse({'error': 'Brak tłumaczenia'}, status=404)
    
    
    if lang == "sl":
        lang = "hr" # Brak wsparcia od Google TTS dla języka Słoweńskiego, Inne TTS brzmią robotycznie
    print(translation)
    tts = gTTS(text=translation.content, lang=lang)
    tts_io = BytesIO()
    tts.write_to_fp(tts_io)
    tts_io.seek(0)

    audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
    with open(audio_path, "wb") as f:
        f.write(tts_io.read())

    audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")
    if lang != "pl":
        translation_obj = sentence
    else:
        translation_obj = sentence.translations.filter(language__code=user.profile.native_language).first()
    


    return JsonResponse({
        'mode': 'repeat',
        'audio_url': audio_url,
        'sentence': {
            'id': sentence.id,
            'content': translation_obj.content if translation_obj else "Brak tłumaczenia",
            'level': sentence.level,
            'category': sentence.category.name if sentence.category else None
        }
    })

@login_required
def translate(request):
    user = request.user
    sentence = choose_sentence(user=user, mode="translate")
    
    if not sentence:
        return JsonResponse({'error': 'Brak dostępnych zdań'}, status=404)
    lang = user.profile.target_language
    if lang != "pl":
        translation_obj = sentence
    else:
        translation_obj = sentence.translations.filter(language__code=user.profile.native_language).first()

    return JsonResponse({
        "mode": "translate",
        "sentence": {
            "id": sentence.id,
            "content": translation_obj.content if translation_obj else "Brak tłumaczenia",
            "level": sentence.level,
            "category": sentence.category.name if sentence.category else None
        }
    })

from django.views.decorators.csrf import csrf_exempt
from gtts import gTTS
from io import BytesIO
from googletrans import Translator

@csrf_exempt
@login_required
def conversation_start(request):
    # Ustawienie początkowej historii
    ai_message = "Hi, how are You? What topic would You like to talk on?"


   
    lang = request.user.profile.target_language

    translator = Translator()
    try:
        translation_result = translator.translate(ai_message, src="en", dest=lang)
        translated = translation_result.text
    except Exception as e:
        translated = "Błąd tłumaczenia."
    
    request.session['chat_history'] = [
        {"role": "system", "content": (
            "You are a native speaker of " + lang + 
            ". Talk only in that language. Your messages are short (max 15 words), helpful, "
            "correct user grammar subtly, and suggest related vocabulary. Keep the conversation flowing. Always set a question on the end."
        )},
        {"role": "assistant", "content": translated}  # Można dynamicznie
    ]
    # Konwersja do audio
    ai_response = request.session['chat_history'][-1]["content"]

    lang = request.user.profile.target_language
    if lang == "sl":
        lang = "hr"

    tts = gTTS(text=ai_response, lang=lang)
    tts_io = BytesIO()
    tts.write_to_fp(tts_io)
    tts_io.seek(0)

    audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
    with open(audio_path, "wb") as f:
        f.write(tts_io.read())
    audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")

    return JsonResponse({
        "mode": "conversation",
        "audio_url": audio_url,
        "message": ai_response
    })


import g4f  

@csrf_exempt
@login_required
def conversation_respond(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        audio_file = request.FILES['audio']
        user = request.user
        lang = user.profile.target_language
        user_id = user.id

        file_path = f"/tmp/whisper/audio_{user_id}.wav"
        with open(file_path, "wb") as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        transcription = transcribe_audio(file_path, lang)
        os.remove(file_path)

        # Historia rozmowy z sesji
        if 'chat_history' not in request.session:
            request.session['chat_history'] = []

        request.session['chat_history'].append({"role": "user", "content": transcription})

        request.session['chat_history'] = request.session['chat_history'][-10:]
        # **Tworzymy prompt do AI**
        
        messages = [{"role": "system", "content": f"You are a native speaker of {lang}. \
                  You answer only in {lang}. Correct mistakes in a subtle way, \
                  but also respond as in a conversation. Your response MUST be short \
                  (maximum 15 words). Be very concise. Keep the conversation going and suggest new words \
                  related to the topic."}]
        messages += request.session['chat_history']
 

        try:
            odpowiedz_ai = g4f.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                max_tokens=40,
            )
        except Exception as e:
            odpowiedz_ai = None


        # **Zapisujemy odpowiedź AI w historii**
        request.session['chat_history'].append({"role": "assistant", "content": odpowiedz_ai})
        request.session.modified = True  # Zapisujemy zmiany w sesji
        if lang == "sl":
            lang = "hr"
        tts = gTTS(text=odpowiedz_ai, lang=lang)
        tts_io = BytesIO()
        tts.write_to_fp(tts_io)
        tts_io.seek(0)

        audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
        with open(audio_path, "wb") as f:
            f.write(tts_io.read())
        audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")

        return JsonResponse({
            "transkrypcja": transcription,
            "odpowiedz_ai": odpowiedz_ai,
            "audio_url": audio_url
        })

    return JsonResponse({'error': 'Błędne żądanie'}, status=400)




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
        user = request.user
        lang = user.profile.target_language
        if lang != "pl":
            translation = sentence.translations.filter(language__code=lang).first().content
        else:
            translation = sentence.content

        score = calculate_similarity(transcription, translation)

        
        mode = request.POST.get('mode')
    
        # Jeśli wynik > 40%, uznajemy odpowiedź za poprawną
        if score > 40:
            update_sentence_progress(user=request.user, sentence=sentence, mode=mode, score=score)
        else:
            score = "Niepoprawna transkrypcja, powtórz nagranie"
        translation_obj = sentence.translations.filter(language__code=user.profile.target_language).first()
        content_text = sentence.content if user.profile.target_language == "pl" else (translation_obj.content if translation_obj else "Brak tłumaczenia")

        return JsonResponse({
            'transkrypcja': transcription,
            'sentence': content_text,
            'translation': translation,
            'levenshtein_score': score
        })

    return JsonResponse({'error': 'Niepoprawne zapytanie'}, status=400)



WHISPER_AUDIO_DIR = "/tmp/whisper"  # katalog zamontowany w docker-compose


from django.conf import settings

def upload_audio(request):
    audio_file = request.FILES['audio']
    user = request.user
    user_id = user.id if user.is_authenticated else "anon"
    lang = user.profile.target_language

    # Plik o nazwie zależnej od użytkownika
    file_name = f"audio_{user_id}.wav"
    file_path = os.path.join(WHISPER_AUDIO_DIR, file_name)

    # Zapisujemy plik (nadpisuje poprzedni)
    with open(file_path, 'wb') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)
    transcription = transcribe_audio(file_path, lang)

    try:
        os.remove(file_path)
    except Exception as e:
        print(f"⚠️ Nie udało się usunąć pliku audio: {e}")

    return transcription


def transcribe_audio(file_path, lang):
    result = whisper_model.transcribe(file_path, language=lang)
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

    # # ⬇️ Oblicz średni similarity score
    # average_similarity = all_progress.aggregate(avg=models.Avg('last_similarity_score'))['avg'] or 0.0

    # # ⬇️ Poziomy CEFR
    # CEFR_LEVELS = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    # current_index = CEFR_LEVELS.index(category_progress.level)

    # # ⬇️ Reguły zmiany poziomu
    # if average_similarity >= 0.8 and current_index < len(CEFR_LEVELS) - 1:
    #     category_progress.level = CEFR_LEVELS[current_index + 1]
    # elif average_similarity < 0.4 and current_index > 0:
    #     category_progress.level = CEFR_LEVELS[current_index - 1]
    # # else: poziom pozostaje bez zmian

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
        "is_mastered": progress.is_mastered_translate,
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
        selected_categories = request.data.get('selected_categories', [])
        # Dezaktywuj wszystkie stare
        UserCategoryPreference.objects.filter(user=user).update(is_active=False)

        # Aktywuj wybrane
        for cat_id in selected_categories:
            pref, created = UserCategoryPreference.objects.get_or_create(user=user, category_id=cat_id)
            pref.is_active = True
            pref.save()

        return Response({"status": "preferences updated"})