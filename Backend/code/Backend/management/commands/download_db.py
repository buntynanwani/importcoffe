from django.core.management.base import BaseCommand
from Backend.proposed_hospitals_database import insert_hospitals_into_object

class Command(BaseCommand):
    help = 'Insert hospitals into the database'

    def handle(self, *args, **kwargs):
        insert_hospitals_into_object()
        self.stdout.write(self.style.SUCCESS('Successfully inserted hospitals into the database'))

