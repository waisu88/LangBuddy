from Levenshtein import distance as levenshtein

def calculate_similarity(transcription, translation):
    distance = levenshtein(transcription, translation)
    score = (1 - distance / max(len(transcription), len(translation))) * 100
    return score

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