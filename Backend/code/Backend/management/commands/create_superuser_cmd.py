from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Create or update a superuser non-interactively'

    def handle(self, *args, **options):
        User = get_user_model()
        # Support both DJANGO_SUPERUSER (legacy) and DJANGO_SUPERUSER_USERNAME (explicit)
        username = os.environ.get('DJANGO_SUPERUSER') or os.environ.get('DJANGO_SUPERUSER_USERNAME') or 'admin'
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL') or 'admin@example.com'
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD') or 'adminpassword'

        username_field = getattr(User, 'USERNAME_FIELD', 'username')
        lookup = {username_field: username}

        if not User.objects.filter(**lookup).exists():
            create_kwargs = {username_field: username}
            if username_field != 'email':
                create_kwargs['email'] = email
            User.objects.create_superuser(**create_kwargs, password=password)
            self.stdout.write(self.style.SUCCESS(f'Created superuser {username}'))
        else:
            user = User.objects.get(**lookup)
            if hasattr(user, 'email'):
                user.email = email
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Updated superuser {username}'))
