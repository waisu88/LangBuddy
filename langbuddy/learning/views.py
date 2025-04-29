import random
from languages.models import Sentence

def get_random_sentence(language, level):
    sentences = Sentence.objects.filter(language=language, level=level)
    return random.choice(sentences) if sentences.exists() else None


# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated
# from .models import LearningSession, UserProgress
# from languages.models import Language, Sentence, Translation
# from .serializers import LearningSessionSerializer
# from .utils.similarity import calculate_similarity

# class LearningView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         language_code = request.data.get('language')
#         level = request.data.get('level')

#         # Znalezienie języka
#         try:
#             language = Language.objects.get(code=language_code)
#         except Language.DoesNotExist:
#             return Response({'error': 'Invalid language code'}, status=400)

#         # Losowanie zdania
#         sentence = get_random_sentence(language, level)
#         if not sentence:
#             return Response({'error': 'No sentences available for this level'}, status=404)

#         return Response({
#             'sentence_id': sentence.id,
#             'content': sentence.content,
#             'level': sentence.level
#         })

# class TranslationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         sentence_id = request.data.get('sentence_id')
#         user_translation = request.data.get('user_translation')

#         try:
#             sentence = Sentence.objects.get(id=sentence_id)
#             correct_translation = Translation.objects.filter(sentence=sentence).first()

#             if not correct_translation:
#                 return Response({'error': 'No translation available'}, status=404)

#             # Obliczanie podobieństwa
#             similarity_score = calculate_similarity(user_translation, correct_translation.content)
#             is_correct = similarity_score > 80.0

#             # Zapis wyników
#             session = LearningSession.objects.create(
#                 user=user,
#                 sentence=sentence,
#                 user_translation=user_translation,
#                 correct_translation=correct_translation,
#                 is_correct=is_correct,
#                 similarity_score=similarity_score
#             )

#             # Aktualizacja postępów
#             progress, _ = UserProgress.objects.get_or_create(user=user, language=sentence.language, level=sentence.level)
#             progress.attempts += 1
#             if is_correct:
#                 progress.score += 1
#             progress.save()

#             return Response({'is_correct': is_correct, 'similarity_score': similarity_score})
#         except Sentence.DoesNotExist:
#             return Response({'error': 'Sentence not found'}, status=404)

# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAuthenticated

# from languages.models import Sentence, Translation
# from .utils.similarity import calculate_similarity

# class EvaluateTranslationView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         user = request.user
#         sentence_id = request.data.get('sentence_id')
#         user_translation = request.data.get('user_translation')

#         if not sentence_id or not user_translation:
#             return Response({'error': 'sentence_id i user_translation są wymagane'}, status=400)

#         try:
#             sentence = Sentence.objects.get(id=sentence_id)
#             correct_translation = Translation.objects.filter(sentence=sentence).first()

#             if not correct_translation:
#                 return Response({'error': 'Brak dostępnego tłumaczenia'}, status=404)

#             # Obliczanie podobieństwa
#             similarity_score = calculate_similarity(user_translation, correct_translation.content)
#             is_correct = similarity_score >= 80.0

#             # Zapis do LearningSession
#             learning_session = LearningSession.objects.create(
#                 user=user,
#                 sentence=sentence,
#                 user_translation=user_translation,
#                 correct_translation=correct_translation,
#                 is_correct=is_correct,
#                 similarity_score=similarity_score
#             )

#             return Response({
#                 'sentence': sentence.content,
#                 'user_translation': user_translation,
#                 'correct_translation': correct_translation.content,
#                 'similarity_score': similarity_score,
#                 'is_correct': is_correct,
#             })

#         except Sentence.DoesNotExist:
#             return Response({'error': 'Nie znaleziono zdania'}, status=404)




"""Widoki funkcji zamienione poniżej na klas oraz DRF"""

"""
Widoki budowane samemu

"""
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
        progress_subquery = UserSentenceProgress.objects.none().values('repeat_attempts')  # fallback

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
    """PROBNE PRINTY"""
    print(sentence.content)
    print(sentence.translations.filter(language__code="hr").first().content)
    
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

import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from difflib import SequenceMatcher
from learning.models import UserProgress
from languages.models import Sentence, Translation
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

        # Tu możesz też np. zaktualizować UserSentenceProgress
        
        mode = request.POST.get('mode')
        update_sentence_progress(user=request.user, sentence=sentence, mode=mode, score=score)

        return JsonResponse({
            'transkrypcja': transcription,
            'sentence': sentence.content,
            'translation': translation,
            'levenshtein_score': score
        })

    return JsonResponse({'error': 'Niepoprawne zapytanie'}, status=400)


def upload_audio(request):
    audio_file = request.FILES['audio']
    file_path = os.path.join("media", audio_file.name)

    # Zapisujemy plik
    with open(file_path, 'wb') as f:
        for chunk in audio_file.chunks():
            f.write(chunk)

    # Transkrypcja
    return transcribe_audio(file_path)


def transcribe_audio(file_path):
    result = whisper_model.transcribe(file_path, language="hr")
    transcription = result['text'].strip()
    return transcription

from Levenshtein import distance as levenshtein

def calculate_similarity(transcription, translation):
    distance = levenshtein(transcription, translation)
    score = (1 - distance / max(len(transcription), len(translation))) * 100
    return score


def update_sentence_progress(user, sentence, mode, score):
    progress, created = UserSentenceProgress.objects.get_or_create(user=user, sentence=sentence)
    progress.update_progress(similarity_score=score, attempt_type=mode)

    return Response({
        "status": "updated",
        "is_mastered": progress.is_mastered,
        "accuracy": progress.accuracy()
    })





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


# from django.db.models import Q, F, OuterRef, Subquery, IntegerField, Value as V
# from django.db.models.functions import Coalesce

# def choose_sentence(user, mode="repeat"):
#     # 1. Sprawdzenie globalnego poziomu użytkownika
#     user_progress = UserProgress.objects.filter(user=user).first()
#     level = user_progress.global_level if user_progress else 'B1'


#     # 2. Sprawdzenie preferowanych kategorii użytkownika
#     preferred_categories = UserCategoryPreference.objects.filter(
#         user=user,
#         is_active=True
#     ).values_list('category_id', flat=True)
    


#     # 3. Wybór zdań pasujących do poziomu użytkownika oraz wybranych kategorii
    
#     # TODO Tutaj możnaby dodać miejsce do zapamiętania kategorii, żeby następne 
#     # zdanie w danej sesji było z tej samej kategorii o ile się nie wyczerpały
    
#     if not preferred_categories:
#         base_sentences = Sentence.objects.all()
#     else:
#         base_sentences = Sentence.objects.filter(
#             level=level,
#             category_id__in=preferred_categories
#         )

#     user_progress_subquery = UserSentenceProgress.objects.filter(
#         user=user,
#         sentence=OuterRef('pk'),
#         is_mastered=False  # <-- wyklucz opanowane
#     )

#     # 5. Annotacja liczby prób — domyślnie 0
#     if mode == "repeat":
#         annotated = base_sentences.annotate(
#             attempts=Coalesce(Subquery(user_progress_subquery.values('repeat_attempts')[:1]), V(0), output_field=IntegerField())
#         )
#     elif mode == "translate":
#         annotated = base_sentences.annotate(
#             attempts=Coalesce(Subquery(user_progress_subquery.values('translate_attempts')[:1]), V(0), output_field=IntegerField())
#         )
#     else:
#         annotated = base_sentences.annotate(
#             attempts=V(0, output_field=IntegerField())
#         )

#     # 6. Posortuj po liczbie prób rosnąco, a w razie remisu losowo
#     sentence = annotated.order_by('attempts', '?').first()
#     return sentence





# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework import status
# from .models import Sentence
# from languages.serializers import SentenceSerializer
# from .whisper_model import model as whisper_model
# from .utils import calculate_similarity
# # choose_sentence  # przenieśmy to dla porządku do utils.py
# from django.conf import settings
# import os
# from gtts import gTTS
# from io import BytesIO

# class RepeatAPIView(APIView):
#     def get(self, request):
#         user = request.user
#         sentence = choose_sentence(user=user, mode="repeat")
#         if not sentence:
#             return Response({'error': 'Brak dostępnych zdań'}, status=status.HTTP_404_NOT_FOUND)

#         translation = sentence.translations.filter(language__code="hr").first()
#         if not translation:
#             return Response({'error': 'Brak tłumaczenia'}, status=status.HTTP_404_NOT_FOUND)

#         tts = gTTS(text=translation.content, lang="hr")
#         tts_io = BytesIO()
#         tts.write_to_fp(tts_io)
#         tts_io.seek(0)

#         audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
#         with open(audio_path, "wb") as f:
#             f.write(tts_io.read())

#         audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")

#         return Response({
#             'mode': 'repeat',
#             'audio_url': audio_url,
#             'sentence': SentenceSerializer(sentence).data
#         })

# class TranslateAPIView(APIView):
#     def get(self, request):
#         user = request.user
#         sentence = choose_sentence(user=user, mode="translate")
#         if not sentence:
#             return Response({'error': 'Brak dostępnych zdań'}, status=status.HTTP_404_NOT_FOUND)

#         return Response({
#             'mode': 'translate',
#             'sentence': SentenceSerializer(sentence).data
#         })

# class CheckAnswerAPIView(APIView):
#     def post(self, request):
#         if 'audio' not in request.FILES:
#             return Response({'error': 'Brak pliku audio'}, status=status.HTTP_400_BAD_REQUEST)

#         transcription = self.upload_audio(request)

#         sentence_id = request.data.get('sentence_id')
#         if not sentence_id:
#             return Response({'error': 'Brak ID zdania'}, status=status.HTTP_400_BAD_REQUEST)

#         try:
#             sentence = Sentence.objects.get(id=sentence_id)
#         except Sentence.DoesNotExist:
#             return Response({'error': 'Nie znaleziono zdania'}, status=status.HTTP_404_NOT_FOUND)

#         translation = sentence.translations.filter(language__code="hr").first()
#         if not translation:
#             return Response({'error': 'Brak tłumaczenia'}, status=status.HTTP_404_NOT_FOUND)

#         score = calculate_similarity(transcription, translation.content)

#         return Response({
#             'transkrypcja': transcription,
#             'sentence': sentence.content,
#             'translation': translation.content,
#             'levenshtein_score': score
#         })

#     def upload_audio(self, request):
#         audio_file = request.FILES['audio']
#         file_path = os.path.join(settings.MEDIA_ROOT, audio_file.name)

#         with open(file_path, 'wb') as f:
#             for chunk in audio_file.chunks():
#                 f.write(chunk)

#         return self.transcribe_audio(file_path)

#     def transcribe_audio(self, file_path):
#         result = whisper_model.transcribe(file_path, language="hr")
#         transcription = result['text'].strip()
#         return transcription





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