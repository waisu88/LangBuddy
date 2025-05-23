import json
from django.core.management.base import BaseCommand
from languages.models import Sentence, Translation

class Command(BaseCommand):
    help = "Eksportuj zdania i tłumaczenia do pliku JSON"

    def add_arguments(self, parser):
        parser.add_argument('--lang', required=True, help="Kod języka docelowego (np. 'cs', 'es')")
        parser.add_argument('--output', required=True, help="Ścieżka pliku wynikowego JSON")

    def handle(self, *args, **options):
        lang_code = options['lang']
        output_path = options['output']

        data = {}

        sentences = Sentence.objects.select_related("language", "category").all()

        sentence_list = []

        for sentence in sentences:
            try:
                translation = sentence.translations.get(language__code=lang_code)

                sentence_list.append({
                    "pl": sentence.content,
                    lang_code: translation.content
                })

            except Translation.DoesNotExist:
                continue  # pomiń zdania bez tłumaczenia na dany język

        if sentence_list:
            data["category"] = sentence.category.name if sentence_list else "Bez kategorii"
            data["level"] = sentence.level
            data["sentences"] = sentence_list

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.stdout.write(self.style.SUCCESS(f"Zapisano {len(sentence_list)} zdań do {output_path}"))
        else:
            self.stdout.write(self.style.WARNING("Nie znaleziono żadnych tłumaczeń dla podanego języka."))
