"""
Management command to run the Shadow Founder AI check.
Usage: python manage.py run_shadow_founder
Schedule with cron or task scheduler for periodic execution.
"""
from django.core.management.base import BaseCommand
from agents.services.shadow_founder import check_and_intervene


class Command(BaseCommand):
    help = "Run Shadow Founder AI to check idle squads and intervene"

    def handle(self, *args, **options):
        self.stdout.write("Running Shadow Founder check...")
        actions = check_and_intervene()
        if actions:
            for action in actions:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Intervened: {action.squad.name} → {action.payload.get('message', '')[:60]}"
                    )
                )
            self.stdout.write(self.style.SUCCESS(f"Total interventions: {len(actions)}"))
        else:
            self.stdout.write(self.style.NOTICE("No idle squads found. All healthy."))
