# Diagrama de entidades (textual)

UUIDs como identificadores públicos em todos os models principais. Constraints,
índices e unique constraints aplicados no banco.

## accounts
```
User(email login, username, role[member|platform_admin], email_verified)
  1─1 UserProfile(display_name, bio, avatar, avatar_key, referral_code, referred_by→User)
  1─1 UserPreference(theme, default_format, locale)
Friendship(requester→User, addressee→User, status[pending|accepted])   uniq(pair)
FavoriteCard(user→User, card→Card)                                     uniq(user,card)
```

## cards / imports
```
CardSet(code, name, release_date, external_source/id)
Card(name, normalized_name, grade, power, shield, critical, card_type, trigger,
     nation, clan, race, keywords, rules_data, equivalence_strategy)
  1─* CardPrinting(card_number, set→CardSet, rarity, language, finish, image_url, price)
  1─* CardImage, CardExternalIdentifier, CardFormatLegality, CardPriceHistory
CardEquivalenceGroup 1─* CardEquivalenceMember →Card
DataSource(key, base_url, rate_limit) 1─* ImportBatch(kind, status, metrics)
  ImportBatch 1─* RawImportPayload(payload bruto, auditável)
```

## collection
```
UserCollectionItem(user→User, card→Card)              uniq(user,card)
  1─* CollectionPrinting(printing→CardPrinting, quantity, condition, language, finish, price_paid)
WishlistItem(user, card, priority)   TradeItem(user, printing, quantity)
```

## formats
```
GameFormat(code) 1─* FormatRuleVersion(version, valid_from/until)
  FormatRuleVersion 1─* FormatZoneRule ; 1─1 FormatTriggerRule ; 1─1 FormatConstructionRule ; 1─* FormatException
```
> O app `powerlevel` (PowerLevelScale / CardPowerLevel / History / TournamentPowerPolicy)
> foi **removido na v2.0**. "Força" agora é `Deck.power_stars` + a nota por deck do
> campeonato (ver abaixo).

## banlists
```
Banlist(category[official|community|tournament_custom], format_code, owner→User, forked_from)
  1─* BanlistVersion(version, status, effective_date)
    1─* BanlistEntry(restriction_type, card→Card?, group→RestrictionGroup?, limit_value)
      BanlistEntry 1─* RestrictionCondition(type, value)   ← DECK_DEPENDENT
    1─* RestrictionGroup(kind[choice|max_distinct|max_total], limit_value)
      1─* RestrictionGroupMember →Card
BanlistLike / BanlistFavorite / BanlistComment
```

## decks
```
Deck(owner→User, format_code, visibility, power_stars[1–5, dono do deck],
     cover_printing, forked_from, current_version)
  1─* DeckVersion(version_number) 1─* DeckEntry(card→Card, preferred_printing, zone, quantity)
  1─* DeckLike / DeckFavorite / DeckComment / DeckFork
DeckSnapshot(deck, payload, content_hash)   DeckTag(M2M Deck)
```

## tournaments
```
Tournament(organizer→User, format_code, banlist→Banlist, banlist_version_number,
           bracket_type, visibility, best_of, ...
           kind[standard|roster],  ← modo campeonato quando "roster":
           format_kind[points|bracket|hybrid], seed_source, rounds_count, hybrid_advance_count,
           decks_per_player, power_cap, min/max_deck_power,
           deck_selection_mode, random_options_count, draw_timing,
           roster_visibility, reveal_lists_after_end,
           ace_enabled, ace_rule, ace_reveal, ace_required,
           allow_draws, points_win/draw/loss/bye)
  1─* TournamentStaff / TournamentRegistration / TournamentParticipant
  1─1 TournamentRulesSnapshot(payload, content_hash)          ← congelado no lock
  1─* TournamentDeckSubmission(participant, snapshot→DeckSnapshot, content_hash, validation, locked)  ← modo clássico
  1─* TournamentCheckIn
  1─* TournamentStage(kind) 1─* TournamentRound 1─* TournamentMatch
        TournamentMatch(participant_a/b, winner, state, score_a/b, next_match/slot,
                        loser_next_match/slot, bracket, is_draw)   ← elim/swiss/RR/double
          1─* TournamentGame ; 1─* MatchReport ; 1─* MatchDispute
          1─* MatchDeckSelection(participant, roster_deck?, method, confirmed, revealed, is_ace_used, options[], eligible[])  uniq(match,participant)
  1─* TournamentStanding(rank, wins, losses, draws, points, tiebreaks)
  1─* TournamentAuditLog(action, actor, payload)

  ── modo campeonato (kind="roster") ──
  1─* TournamentRoster(participant 1─1, status, power_used, is_over_cap, confirmed_at)
        1─* RosterDeck(source_deck→Deck, snapshot→DeckSnapshot, power[dono], power_by→User,
                       is_ace, banlist_valid, is_valid, label, slot, locked)  uniq(roster,source_deck)
        1─* RosterDeckSequence(round_number, roster_deck, revealed)  ← predetermined_order
        1─* AceEvent(match?, kind[used|replaced_draw|revealed])
  1─* DeckDrawLog(round, participant, result_deck?, eligible[], options[], rule, admin_intervention, admin)  ← imutável
  1─* TournamentPenalty(participant, match?, kind, points, reason, issued_by)
```

## common
```
AuditLog(action, actor→User, target_type/id, payload, source)   ← cross-cutting append-only
BaseModel = UUID + created_at/updated_at ; SoftDeleteModel = deleted_at
```
