# # from django.shortcuts import render
# # from django.http import JsonResponse
# # from django.views.decorators.csrf import csrf_exempt
# # import whisper
# # import os
# # from django.conf import settings
# # from languages.models import Sentence, Translation
# # from Levenshtein import ratio  # Levenshtein to biblioteka do porównywania tekstów
# # import g4f
# # from io import BytesIO
# # from gtts import gTTS

# # # Funkcja widoku, która obsługuje nagrywanie
# # def get_record_view(request):
# #     return render(request, "main.html")

# # @csrf_exempt
# # def upload_audio(request):
# #     if request.method == 'POST' and request.FILES.get('audio'):
# #         plik_audio = request.FILES['audio']
# #         sciezka_audio = os.path.join("media", plik_audio.name)
        
# #         # Zapisujemy plik audio
# #         with open(sciezka_audio, 'wb') as f:
# #             for chunk in plik_audio.chunks():
# #                 f.write(chunk)

# #         # **Transkrypcja audio za pomocą Whisper**
# #         model = whisper.load_model("base")
# #         result = model.transcribe(sciezka_audio, language="hr")
# #         transkrypcja = result['text']

# #         # **Znajdujemy poprawne tłumaczenie z bazy danych**
# #         correct_translation = Translation.objects.filter(content__icontains=transkrypcja).first()

# #         if correct_translation:
# #             # **Porównanie transkrypcji z tłumaczeniem za pomocą Levenshteina**
# #             lev_score = ratio(transkrypcja.lower(), correct_translation.content.lower()) * 100

# #             if lev_score > 80:
# #                 # **Tłumaczenie uznane za poprawne**
# #                 response = {
# #                     'transkrypcja': transkrypcja,
# #                     'result': 'Poprawne tłumaczenie',
# #                     'levenshtein_score': lev_score,
# #                 }
# #             elif lev_score >= 50:
# #                 # **Sugestia poprawy tłumaczenia**
# #                 response = {
# #                     'transkrypcja': transkrypcja,
# #                     'result': 'Tłumaczenie wymaga poprawy',
# #                     'levenshtein_score': lev_score,
# #                 }
# #             else:
# #                 # **Wysyłamy do GPT-4 w celu sprawdzenia sensowności**
# #                 messages = [
# #                     {"role": "system", "content": "Sprawdź, czy to tłumaczenie ma sens. Oceń poprawność tłumaczenia."},
# #                     {"role": "user", "content": transkrypcja}
# #                 ]

# #                 odpowiedz_ai = g4f.ChatCompletion.create(
# #                     model="gpt-4",
# #                     messages=messages,
# #                     max_tokens=100
# #                 )

# #                 response = {
# #                     'transkrypcja': transkrypcja,
# #                     'result': 'Tłumaczenie niepoprawne, wysyłam do GPT',
# #                     'levenshtein_score': lev_score,
# #                     'gpt_response': odpowiedz_ai['choices'][0]['message']['content']
# #                 }

# #         else:
# #             # Jeśli nie znaleziono poprawnego tłumaczenia w bazie
# #             response = {
# #                 'error': 'Nie znaleziono poprawnego tłumaczenia w bazie danych.',
# #             }

# #         return JsonResponse(response)
    
# #     return JsonResponse({'error': 'Błędne żądanie'}, status=400)



# from django.shortcuts import render
# from django.http import JsonResponse
# from django.views.decorators.csrf import csrf_exempt
# import whisper
# import os
# from django.conf import settings
# from languages.models import Sentence, Translation
# from Levenshtein import ratio  # Levenshtein to biblioteka do porównywania tekstów
# import g4f
# from io import BytesIO
# from gtts import gTTS

# # Funkcja widoku, która obsługuje nagrywanie
# def get_record_view(request):
#     zdanie = Translation.objects.order_by('?').first()  # Losowanie zdania
#     request.session['zdanie_id'] = zdanie.id  # Zapisz ID w sesji
#     return render(request, "main.html", {"zdanie": zdanie})

# @csrf_exempt
# def upload_audio(request):
#     if request.method == 'POST' and request.FILES.get('audio'):
#         plik_audio = request.FILES['audio']
#         sciezka_audio = os.path.join("media", plik_audio.name)
#         # Pobranie ID zdania z sesji
#         zdanie_id = request.session.get('zdanie_id')
#         if not zdanie_id:
#             return JsonResponse({'error': 'Brak ID zdania w sesji'}, status=400)
        
#         try:
#             zdanie = Translation.objects.get(id=zdanie_id).content
#         except Translation.DoesNotExist:
#             return JsonResponse({'error': 'Nie znaleziono tłumaczenia w bazie danych'}, status=404)

#         # Zapisujemy plik audio
#         with open(sciezka_audio, 'wb') as f:
#             for chunk in plik_audio.chunks():
#                 f.write(chunk)

#         # **Transkrypcja audio za pomocą Whisper**

#         model = whisper.load_model("base")
 
#         result = model.transcribe(sciezka_audio, language="hr")
     
#         transkrypcja = result['text']

#         # **Znajdujemy poprawne tłumaczenie z bazy danych**
#         lev_score = ratio(transkrypcja.lower(), zdanie.lower()) * 100



#         # if correct_translation:
#         #     # **Porównanie transkrypcji z tłumaczeniem za pomocą Levenshteina**
#         #     lev_score = ratio(transkrypcja.lower(), correct_translation.content.lower()) * 100

#         #     if lev_score > 80:
#         #         # **Tłumaczenie uznane za poprawne**
#         #         response = {
#         #             'transkrypcja': transkrypcja,
#         #             'result': 'Poprawne tłumaczenie',
#         #             'levenshtein_score': lev_score,
#         #         }
#         #     elif lev_score >= 50:
#         #         # **Sugestia poprawy tłumaczenia**
#         #         response = {
#         #             'transkrypcja': transkrypcja,
#         #             'result': 'Tłumaczenie wymaga poprawy',
#         #             'levenshtein_score': lev_score,
#         #         }
#         #     else:
#         #         # **Wysyłamy do GPT-4 w celu sprawdzenia sensowności**
#         #         messages = [
#         #             {"role": "system", "content": "Sprawdź, czy to tłumaczenie ma sens. Oceń poprawność tłumaczenia."},
#         #             {"role": "user", "content": transkrypcja}
#         #         ]

#         #         odpowiedz_ai = g4f.ChatCompletion.create(
#         #             model="gpt-4",
#         #             messages=messages,
#         #             max_tokens=100
#         #         )

#         #         response = {
#         #             'transkrypcja': transkrypcja,
#         #             'result': 'Tłumaczenie niepoprawne, wysyłam do GPT',
#         #             'levenshtein_score': lev_score,
#         #             'gpt_response': odpowiedz_ai['choices'][0]['message']['content']
#         #         }

#         # else:
#         #     # Jeśli nie znaleziono poprawnego tłumaczenia w bazie
#         #     response = {
#         #         'error': 'Nie znaleziono poprawnego tłumaczenia w bazie danych.',
#         #     }
#         response = {
#                     'transkrypcja': transkrypcja,
#                     'translation': zdanie,
#                     # 'result': 'Tłumaczenie niepoprawne, wysyłam do GPT',
#                     'levenshtein_score': lev_score,
#                     # 'gpt_response': odpowiedz_ai['choices'][0]['message']['content']
#                 }
#         return JsonResponse(response)
    
#     return JsonResponse({'error': 'Błędne żądanie'}, status=400)

import os
import whisper
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from difflib import SequenceMatcher
from learning.models import LearningSession, UserProgress
from languages.models import Sentence, Translation

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
        model = whisper.load_model("base")
        result = model.transcribe(file_path, language="hr")
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




from django.http import JsonResponse
import random
from languages.models import Sentence, Translation

def get_sentence(request):
    user = request.user
    mode = request.GET.get('mode', 'repeat')  # Możemy pobrać tryb z URL-a

    # 🟢 **Wybór zdania z uwzględnieniem poziomu użytkownika**
    user_progress = user.progress.filter(language__code='hr').first()
    user_level = user_progress.level if user_progress else 'B1'

    sentences = Sentence.objects.filter(language__code='pl')
    
    # sentences = Sentence.objects.filter(language__code='pl', level=user_level)
    if not sentences.exists():
        return JsonResponse({'error': 'Brak zdań do nauki.'})

    sentence = random.choice(sentences)

    # 🟢 **Dla trybu tłumaczenia zwracamy odpowiednie tłumaczenie**
    translation = Translation.objects.filter(sentence=sentence, language__code='hr').first()

    return JsonResponse({
        'id': sentence.id,
        'sentence': sentence.content,
        'mode': mode,
        'correct_translation': translation.content if translation else None
    })
