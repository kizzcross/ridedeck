"""Roster-championship presets — one-click configurations that pre-fill the
creation wizard. Each preset is a partial set of Tournament config fields."""
from __future__ import annotations

from .choices import (
    AceRule,
    DeckSelectionMode,
    FormatKind,
    TournamentKind,
)

PRESETS = [
    {
        "code": "power_rotation",
        "name": "Power Rotation",
        "description": "4 decks, cap 15, rotação obrigatória, suíço, campeão por pontos.",
        "config": {
            "kind": TournamentKind.ROSTER,
            "decks_per_player": 4,
            "power_cap": 15,
            "ace_enabled": False,
            "deck_selection_mode": DeckSelectionMode.RANDOM_ROTATION,
            "format_kind": FormatKind.POINTS,
            "bracket_type": "swiss",
        },
    },
    {
        "code": "ace_challenge",
        "name": "Ace Challenge",
        "description": "Ace ativo: substitui um sorteio 1×; rotação; Ace só como desempate.",
        "config": {
            "kind": TournamentKind.ROSTER,
            "decks_per_player": 4,
            "power_cap": 15,
            "ace_enabled": True,
            "ace_rule": AceRule.REPLACE_DRAW,
            "ace_required": True,
            "deck_selection_mode": DeckSelectionMode.RANDOM_ROTATION,
            "format_kind": FormatKind.POINTS,
            "bracket_type": "swiss",
            "tiebreakers": ["points", "ace_wins", "omw"],
        },
    },
    {
        "code": "random_two",
        "name": "Random Two",
        "description": "Sistema sorteia 2 decks e o jogador escolhe 1; sem repetir até fechar o ciclo.",
        "config": {
            "kind": TournamentKind.ROSTER,
            "decks_per_player": 4,
            "power_cap": 15,
            "ace_enabled": False,
            "deck_selection_mode": DeckSelectionMode.CHOOSE_FROM_RANDOM,
            "random_options_count": 2,
            "format_kind": FormatKind.POINTS,
            "bracket_type": "swiss",
        },
    },
    {
        "code": "full_random",
        "name": "Full Random",
        "description": "Sorteio totalmente aleatório, repetições permitidas. Casual e rápido.",
        "config": {
            "kind": TournamentKind.ROSTER,
            "decks_per_player": 4,
            "power_cap": 15,
            "ace_enabled": False,
            "deck_selection_mode": DeckSelectionMode.RANDOM_FREE,
            "format_kind": FormatKind.POINTS,
            "bracket_type": "swiss",
        },
    },
]
