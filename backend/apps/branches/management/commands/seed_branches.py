from django.core.management.base import BaseCommand
from apps.branches.models import Branch

class Command(BaseCommand):
    help = "Create the initial TechBOK branches if they do not already exist."
    def handle(self, *args, **options):
        branches = [
            {"code": "benin-city", "name": "TechBOK Benin City", "centre_code": "01"},
            {"code": "auchi", "name": "TechBOK Auchi", "centre_code": "02"},
        ]
        for item in branches:
            obj, created = Branch.objects.get_or_create(
                code=item["code"],
                defaults={"name": item["name"], "centre_code": item["centre_code"]},
            )
            if obj.centre_code != item["centre_code"]:
                obj.centre_code = item["centre_code"]
                obj.save(update_fields=["centre_code"])
            self.stdout.write(self.style.SUCCESS(("Created " if created else "Exists: ") + f"{obj.name} ({obj.centre_code})"))
