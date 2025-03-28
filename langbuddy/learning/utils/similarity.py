import Levenshtein

def calculate_similarity(user_translation, correct_translation):
    """
    Oblicza procentowe podobieństwo między tłumaczeniem użytkownika a poprawnym tłumaczeniem.
    """
    user_translation = user_translation.strip().lower()
    correct_translation = correct_translation.strip().lower()

    # Obliczenie odległości Levenshteina
    distance = Levenshtein.distance(user_translation, correct_translation)
    
    # Obliczenie podobieństwa jako procent
    max_length = max(len(user_translation), len(correct_translation))
    if max_length == 0:
        return 100.0

    similarity_score = ((max_length - distance) / max_length) * 100
    return round(similarity_score, 2)
