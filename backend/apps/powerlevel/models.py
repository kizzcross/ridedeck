"""Editorial card power level — REMOVED.

Deck strength is now an owner-chosen 1–5 star rating on the Deck model
(`decks.Deck.power_stars`). This app is kept only as an empty shell so the
historical migration graph (tournaments.0001 depended on it) stays valid; a
delete migration drops all its former tables. No models, endpoints or admin
remain.
"""
