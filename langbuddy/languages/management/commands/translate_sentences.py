import os
from django.core.management.base import BaseCommand
from googletrans import Translator
from languages.models import Sentence, Translation, Language
import time

class Command(BaseCommand):
    help = "Translate all Polish sentences into a specified language and store translations."

    def add_arguments(self, parser):
        parser.add_argument('lang_code', type=str, help='Target language code, e.g., "cs" for Czech or "es" for Spanish')

    def handle(self, *args, **options):
        target_lang_code = options['lang_code'].lower()

        # Inicjalizacja translatora
        translator = Translator()

        # Pobranie języków
        try:
            pl_language = Language.objects.get(code='pl')
        except Language.DoesNotExist:
            self.stderr.write(self.style.ERROR("Brak języka 'pl' w bazie"))
            return

        try:
            target_language, _ = Language.objects.get_or_create(code=target_lang_code)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Błąd podczas pobierania/dodawania języka docelowego: {e}"))
            return

        # Pobranie polskich zdań
        sentences = Sentence.objects.filter(language=pl_language)

        count = 0
        for sentence in sentences:
            # Sprawdź, czy tłumaczenie już istnieje
            if Translation.objects.filter(sentence=sentence, language=target_language).exists():
                continue

            try:
                translated = translator.translate(sentence.content, src='pl', dest=target_lang_code)
                Translation.objects.get_or_create(
                    sentence=sentence,
                    language=target_language,
                    content=translated.text
                )
                count += 1
                time.sleep(0.1)
                print(count)
            except Exception as e:
                self.stderr.write(self.style.WARNING(f"Błąd tłumaczenia '{sentence.content}': {e}"))

        self.stdout.write(self.style.SUCCESS(f"Utworzono {count} tłumaczeń na język '{target_lang_code}'"))

