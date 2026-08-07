"""Development seed data — idempotent.

Grows phase by phase. Phase 1 seeds the three canonical actors:
  * a Platform Admin
  * a Tournament Organizer (a normal member who will own a tournament)
  * a plain Member

All fictional; no protected material is used.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

User = get_user_model()

SEED_USERS = [
    # (email, username, password, role, note)
    ("admin@ridedeck.test", "admin", "adminpass123", "platform_admin", "Platform Admin"),
    ("organizer@ridedeck.test", "organizer", "organizerpass123", "member", "Tournament Organizer"),
    ("player@ridedeck.test", "player", "playerpass123", "member", "Member"),
]


class Command(BaseCommand):
    help = "Load idempotent development seed data."

    def add_arguments(self, parser):
        parser.add_argument("--if-empty", action="store_true",
                            help="Only seed when no seed users exist yet.")

    def handle(self, *args, **options):
        if options.get("if_empty") and User.objects.filter(
            email__in=[u[0] for u in SEED_USERS]
        ).exists():
            self.stdout.write("Seed users already present — skipping (--if-empty).")
            return

        self.seed_users()
        self.seed_catalog()
        self.seed_formats()
        self.seed_banlists()
        self.stdout.write(self.style.SUCCESS("Seed complete."))

    def seed_banlists(self):
        from apps.banlists.choices import BanlistCategory, GroupKind, RestrictionType
        from apps.banlists.models import (
            Banlist,
            BanlistEntry,
            BanlistVersion,
            RestrictionGroup,
            RestrictionGroupMember,
        )
        from apps.cards.models import Card

        if Banlist.objects.exists():
            self.stdout.write("  = Banlists already seeded — skipping.")
            return

        admin = User.objects.filter(role="platform_admin").first()
        organizer = User.objects.filter(username="organizer").first()
        cards = list(Card.objects.order_by("-grade")[:6])
        if not cards:
            return

        def make(name, category, owner, objective=""):
            bl = Banlist.objects.create(name=name, category=category, owner=owner,
                                        format_code="standard", objective=objective)
            v = BanlistVersion.objects.create(banlist=bl, version=1)
            bl.current_version = v
            bl.save()
            return bl, v

        # 1 official banlist
        _, ov = make("Standard — Official Restrictions", BanlistCategory.OFFICIAL, admin,
                     "Restrições oficiais vigentes")
        BanlistEntry.objects.create(version=ov, restriction_type=RestrictionType.LIMIT_TO_1,
                                    card=cards[0])
        # 2 community banlists (one with a Choice Restriction group)
        _, cv1 = make("Budget Brawl", BanlistCategory.COMMUNITY, organizer,
                      "Banlist casual para jogo acessível")
        BanlistEntry.objects.create(version=cv1, restriction_type=RestrictionType.BANNED,
                                    card=cards[1])
        _, cv2 = make("Choice Wars", BanlistCategory.COMMUNITY, organizer,
                      "Demonstra Choice Restriction")
        grp = RestrictionGroup.objects.create(version=cv2, name="Bosses A/B",
                                              kind=GroupKind.CHOICE, limit_value=1)
        RestrictionGroupMember.objects.create(group=grp, card=cards[2])
        RestrictionGroupMember.objects.create(group=grp, card=cards[3])
        BanlistEntry.objects.create(version=cv2,
                                    restriction_type=RestrictionType.CHOICE_RESTRICTION, group=grp)
        self.stdout.write("  + Banlists: 1 oficial + 2 comunitárias (com Choice Restriction)")

    def seed_formats(self):
        from django.core.management import call_command

        call_command("seed_formats")

    def seed_catalog(self):
        """Import the offline fixture catalog (3 sets, 30 fictional cards)."""
        from apps.cards.models import Card
        from apps.imports.services import ImportRunner, ensure_source

        source = ensure_source("fixture", "Development Fixture", config={})
        if Card.objects.exists():
            self.stdout.write("  = Catalog already populated — skipping import.")
            return
        runner = ImportRunner(source, triggered_by="seed")
        runner.import_sets()
        batch = runner.import_cards()
        self.stdout.write(
            f"  + Catalog: {Card.objects.count()} cards imported "
            f"(created={batch.created}, updated={batch.updated})"
        )

    def seed_users(self):
        for email, username, password, role, note in SEED_USERS:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": username, "role": role,
                          "is_staff": role == "platform_admin",
                          "is_superuser": role == "platform_admin",
                          "email_verified": True},
            )
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"  + {note}: {email} / {password}")
            else:
                self.stdout.write(f"  = {note}: {email} (exists)")
