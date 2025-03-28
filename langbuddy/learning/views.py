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

from django.shortcuts import render  
from django.http import JsonResponse     

def exercise_view(request):
    mode = request.GET.get('mode', 'repeat')
    sentence = get_next_sentence(request.user, mode)
    if not sentence:
        return JsonResponse({'error': 'Brak dostępnych zdań'})
    print(mode, sentence)
    context = {
        'mode': mode,
        'sentence': sentence.content
    }
    return render(request, 'exercise.html', context)

from django.db.models import Q

def get_next_sentence(user, mode):
    user_progress = UserProgress.objects.filter(user=user)
    learning_sessions = LearningSession.objects.filter(user=user)

    # Odrzuć zdania, które użytkownik już zna
    known_sentence_ids = learning_sessions.filter(is_correct=True).values_list('sentence_id', flat=True)
    print(mode)
    # Dostosowanie do trybu nauki
    if mode == 'repeat':
        sentences = Sentence.objects.all()
        # sentences = Sentence.objects.filter(
        #     language__code=user.profile.target_language,
        #     level=user.profile.target_language_level
        # ).exclude(id__in=known_sentence_ids).order_by('?')
    elif mode == 'translate':
        sentences = Sentence.objects.filter(
            language__code='pl'
        ).exclude(id__in=known_sentence_ids).order_by('?')
    else:
        return None

    # # Priorytet dla trudniejszych zdań
    # if sentences.exists():
    #     sentences = sentences.order_by('-learning_session__similarity_score')
    for sentence in sentences:
        print(sentence)
    return sentences.first()

