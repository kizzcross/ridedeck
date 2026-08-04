from django.contrib import admin

from .models import (
    Tournament,
    TournamentMatch,
    TournamentParticipant,
    TournamentRound,
    TournamentStage,
)


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ("name", "organizer", "bracket_type", "status", "format_code", "created_at")
    list_filter = ("status", "bracket_type", "format_code")
    search_fields = ("name", "organizer__username")
    raw_id_fields = ("organizer", "banlist", "power_policy")


@admin.register(TournamentParticipant)
class ParticipantAdmin(admin.ModelAdmin):
    list_display = ("tournament", "user", "seed", "status", "final_rank")
    raw_id_fields = ("tournament", "user")


class MatchInline(admin.TabularInline):
    model = TournamentMatch
    extra = 0
    raw_id_fields = ("participant_a", "participant_b", "winner", "next_match")


@admin.register(TournamentRound)
class RoundAdmin(admin.ModelAdmin):
    list_display = ("stage", "number", "name", "status")
    inlines = [MatchInline]


admin.site.register(TournamentStage)
