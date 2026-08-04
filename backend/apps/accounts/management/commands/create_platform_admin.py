"""Create or promote a Platform Admin.

Usage:
    python manage.py create_platform_admin admin@example.com --username admin --password ...

If the user exists, it is promoted. If not, it is created. Password is prompted
securely when omitted.
"""
import getpass

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError

User = get_user_model()


class Command(BaseCommand):
    help = "Create or promote a user to Platform Admin."

    def add_arguments(self, parser):
        parser.add_argument("email")
        parser.add_argument("--username", default=None)
        parser.add_argument("--password", default=None)

    def handle(self, *args, **options):
        email = options["email"].lower()
        username = options["username"] or email.split("@")[0]
        password = options["password"]

        user = User.objects.filter(email=email).first()
        if user:
            user.promote_to_platform_admin()
            self.stdout.write(self.style.SUCCESS(
                f"Promoted existing user {user.username} to Platform Admin."))
            return

        if not password:
            password = getpass.getpass("Password for new Platform Admin: ")
            if not password:
                raise CommandError("A password is required to create a new admin.")

        user = User.objects.create_superuser(
            email=email, username=username, password=password
        )
        self.stdout.write(self.style.SUCCESS(
            f"Created Platform Admin {user.username} <{user.email}>."))
