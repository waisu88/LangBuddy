import random
from languages.models import Sentence

def get_random_sentence(language, level):
    sentences = Sentence.objects.filter(language=language, level=level)
    return random.choice(sentences) if sentences.exists() else None


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import LearningSession, UserProgress
from languages.models import Language, Sentence, Translation
from .serializers import LearningSessionSerializer
from .utils.similarity import calculate_similarity

class LearningView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        language_code = request.data.get('language')
        level = request.data.get('level')

        # Znalezienie języka
        try:
            language = Language.objects.get(code=language_code)
        except Language.DoesNotExist:
            return Response({'error': 'Invalid language code'}, status=400)

        # Losowanie zdania
        sentence = get_random_sentence(language, level)
        if not sentence:
            return Response({'error': 'No sentences available for this level'}, status=404)

        return Response({
            'sentence_id': sentence.id,
            'content': sentence.content,
            'level': sentence.level
        })

class TranslationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        sentence_id = request.data.get('sentence_id')
        user_translation = request.data.get('user_translation')

        try:
            sentence = Sentence.objects.get(id=sentence_id)
            correct_translation = Translation.objects.filter(sentence=sentence).first()

            if not correct_translation:
                return Response({'error': 'No translation available'}, status=404)

            # Obliczanie podobieństwa
            similarity_score = calculate_similarity(user_translation, correct_translation.content)
            is_correct = similarity_score > 80.0

            # Zapis wyników
            session = LearningSession.objects.create(
                user=user,
                sentence=sentence,
                user_translation=user_translation,
                correct_translation=correct_translation,
                is_correct=is_correct,
                similarity_score=similarity_score
            )

            # Aktualizacja postępów
            progress, _ = UserProgress.objects.get_or_create(user=user, language=sentence.language, level=sentence.level)
            progress.attempts += 1
            if is_correct:
                progress.score += 1
            progress.save()

            return Response({'is_correct': is_correct, 'similarity_score': similarity_score})
        except Sentence.DoesNotExist:
            return Response({'error': 'Sentence not found'}, status=404)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import LearningSession
from languages.models import Sentence, Translation
from .utils.similarity import calculate_similarity

class EvaluateTranslationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        sentence_id = request.data.get('sentence_id')
        user_translation = request.data.get('user_translation')

        if not sentence_id or not user_translation:
            return Response({'error': 'sentence_id i user_translation są wymagane'}, status=400)

        try:
            sentence = Sentence.objects.get(id=sentence_id)
            correct_translation = Translation.objects.filter(sentence=sentence).first()

            if not correct_translation:
                return Response({'error': 'Brak dostępnego tłumaczenia'}, status=404)

            # Obliczanie podobieństwa
            similarity_score = calculate_similarity(user_translation, correct_translation.content)
            is_correct = similarity_score >= 80.0

            # Zapis do LearningSession
            learning_session = LearningSession.objects.create(
                user=user,
                sentence=sentence,
                user_translation=user_translation,
                correct_translation=correct_translation,
                is_correct=is_correct,
                similarity_score=similarity_score
            )

            return Response({
                'sentence': sentence.content,
                'user_translation': user_translation,
                'correct_translation': correct_translation.content,
                'similarity_score': similarity_score,
                'is_correct': is_correct,
            })

        except Sentence.DoesNotExist:
            return Response({'error': 'Nie znaleziono zdania'}, status=404)






"""
Widoki budowane samemu

"""
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

import os
from django.conf import settings
from languages.models import Translation

from io import BytesIO
from gtts import gTTS

def repeat(request):
    #TODO Tutaj trzeba będzie wymyśleć logikę dla pobierania zdań w zależności od poziomu użytkownika
    translation = Translation.objects.all().first().content
    tts = gTTS(text=translation, lang="hr")
    audio_path = os.path.join(settings.MEDIA_ROOT, "response.mp3")
    tts_io = BytesIO()
    tts.write_to_fp(tts_io)
    tts_io.seek(0)

    with open(audio_path, "wb") as f:
            f.write(tts_io.read())

    audio_url = os.path.join(settings.MEDIA_URL, "response.mp3")

    context = {
            'audio_url': audio_url,
            'mode': 'repeat'
        }
    return JsonResponse(context)



def translate(request):
    sentence = Sentence.objects.order_by("?").first()
    # translation = sentence.translations.order_by("?").first()
    context = {
        "sentence": sentence.content,
        # "translation": translation.content,
        "mode": "translate"
    }
    return JsonResponse(context)


import os
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from difflib import SequenceMatcher
from learning.models import LearningSession, UserProgress
from languages.models import Sentence, Translation
# import whisper
from .whisper_model import model as whisper_model



@csrf_exempt
def upload_audio(request):
    if request.method == 'POST' and request.FILES.get('audio'):
        # 1️⃣ Pobranie pliku audio
        audio_file = request.FILES['audio']
        file_path = os.path.join("media", audio_file.name)

        # Zapisujemy plik
        with open(file_path, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)

        # 2️⃣ Transkrypcja za pomocą Whisper
        
        result = whisper_model.transcribe(file_path, language="hr")
        transcription = result['text'].strip()
        print(transcription)
        # 3️⃣ Pobranie trybu nauki i zdania
        mode = request.POST.get('mode', 'repeat')  # Domyślnie tryb powtarzania
        sentence_id = request.POST.get('sentence_id')
        sentence = Sentence.objects.filter(id=sentence_id).first()

        # if not sentence:
        #     return JsonResponse({'error': 'Nie znaleziono zdania w bazie danych.'})

        user = request.user
        correct_translation = Translation.objects.filter(sentence=sentence, language__code='hr').first()

        # if mode == "repeat":
        #     score = calculate_similarity(sentence.content, transcription)
        # elif mode == "translate" and correct_translation:
        #     score = calculate_similarity(correct_translation.content, transcription)
        # else:
        #     score = 0  # Dla trybu rozmowy możemy dodać inne kryteria oceny
        score = 0
        # 4️⃣ Zapis sesji nauki
        # LearningSession.objects.create(
        #     user=user,
        #     sentence=sentence,
        #     user_translation=transcription,
        #     correct_translation=correct_translation if mode == "translate" else None,
        #     is_correct=score > 80,  # Poprawne, jeśli wynik >= 80%
        #     similarity_score=score
        # )

        # 5️⃣ Aktualizacja poziomu trudności użytkownika
        # update_user_progress(user, sentence.language, score)

        return JsonResponse({'transkrypcja': transcription, 'score': score})

    return JsonResponse({'error': 'Niepoprawne zapytanie'})


def calculate_similarity(original, user_input):
    return SequenceMatcher(None, original.lower(), user_input.lower()).ratio() * 100

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