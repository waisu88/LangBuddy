import json
from django.core.management.base import BaseCommand
from languages.models import Language, Category, Sentence, Translation


class Command(BaseCommand):
    help = "Load sentences and translations from a JSON file"

    def handle(self, *args, **kwargs):
        file_path = "zdania/hobbyA1.json"  # Możesz zmienić ścieżkę do pliku JSON

        try:
            with open(file_path, encoding="utf-8") as file:
                data = json.load(file)

            category_name = data.get("category", "Bez kategorii")
            category, _ = Category.objects.get_or_create(name=category_name)

            level = data.get("level", "B1")

            pl_language, _ = Language.objects.get_or_create(name="Polish", code="pl")
            hr_language, _ = Language.objects.get_or_create(name="Croatian", code="hr")

            for sentence_pair in data["sentences"]:
                pl_sentence, _ = Sentence.objects.get_or_create(
                    content=sentence_pair["pl"],
                    language=pl_language,
                    category=category,
                    level=level
                )

                Translation.objects.get_or_create(
                    sentence=pl_sentence,
                    language=hr_language,
                    content=sentence_pair["hr"]
                )

            self.stdout.write(self.style.SUCCESS("Dane zostały załadowane pomyślnie!"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Błąd: {e}"))
