import os
import json
from django.core.management.base import BaseCommand
from languages.models import Sentence, Language, Translation

class Command(BaseCommand):
    help = "Wczytaj dodatkowe tłumaczenia (np. czeskie, hiszpańskie) do istniejących zdań po polsku"

    def add_arguments(self, parser):
        parser.add_argument("--lang", required=True, help="Kod języka tłumaczenia (np. 'cs', 'es')")
        parser.add_argument("--input", required=True, help="Ścieżka do pliku JSON z tłumaczeniami")

    def handle(self, *args, **options):
        lang_code = options["lang"]
        file_path = options["input"]

        try:
            with open(file_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Błąd odczytu pliku: {e}"))
            return

        # Upewnij się, że język istnieje
        try:
            translation_language = Language.objects.get(code=lang_code)
        except Language.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Język '{lang_code}' nie istnieje w bazie."))
            return

        pl_language = Language.objects.get(code="pl")
        added = 0
        skipped = 0

        for item in data.get("sentences", []):
            pl_text = item.get("pl")
            translated_text = item.get(lang_code)

            if not pl_text or not translated_text:
                continue

            try:
                sentence = Sentence.objects.get(content=pl_text, language=pl_language)
                obj, created = Translation.objects.get_or_create(
                    sentence=sentence,
                    language=translation_language,
                    defaults={"content": translated_text}
                )
                if created:
                    added += 1
                else:
                    skipped += 1
            except Sentence.DoesNotExist:
                self.stderr.write(self.style.WARNING(f"Polskie zdanie nie istnieje: {pl_text}"))
                continue

        self.stdout.write(self.style.SUCCESS(f"Dodano {added} nowych tłumaczeń."))
        if skipped:
            self.stdout.write(self.style.WARNING(f"Pominięto {skipped} tłumaczeń (już istnieją)."))
