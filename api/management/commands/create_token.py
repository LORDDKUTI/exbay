
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

class Command(BaseCommand):
    help = 'Create JWT access and refresh tokens for a user. Usage: python manage.py create_token --username USERNAME'

    def add_arguments(self, parser):
        parser.add_argument('--username', required=True, help='Username to create tokens for')

    def handle(self, *args, **options):
        username = options['username']
        User = get_user_model()
        user = User.objects.filter(username=username).first()
        if not user:
            self.stderr.write(self.style.ERROR(f"User '{username}' not found."))
            return
        refresh = RefreshToken.for_user(user)
        self.stdout.write(self.style.SUCCESS("ACCESS: " + str(refresh.access_token)))
        self.stdout.write(self.style.SUCCESS("REFRESH: " + str(refresh)))