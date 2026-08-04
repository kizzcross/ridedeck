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

## formats / powerlevel
```
GameFormat(code) 1─* FormatRuleVersion(version, valid_from/until)
  FormatRuleVersion 1─* FormatZoneRule ; 1─1 FormatTriggerRule ; 1─1 FormatConstructionRule ; 1─* FormatException
PowerLevelScale(min,max,descriptions)
CardPowerLevel(card→Card, format_code, value, status, version)  uniq(card,format)
  CardPowerLevelHistory(previous/new_value, admin, justification, source, version)  ← append-only
TournamentPowerPolicy(kind, config) 1─* TournamentPowerPolicyRule
```

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
Deck(owner→User, format_code, visibility, cover_printing, forked_from, current_version)
  1─* DeckVersion(version_number) 1─* DeckEntry(card→Card, preferred_printing, zone, quantity)
  1─* DeckLike / DeckFavorite / DeckComment / DeckFork
DeckSnapshot(deck, payload, content_hash)   DeckTag(M2M Deck)
```

## tournaments
```
Tournament(organizer→User, format_code, banlist→Banlist, banlist_version_number,
           power_policy→TournamentPowerPolicy, bracket_type, visibility, best_of, ...)
  1─* TournamentStaff / TournamentRegistration / TournamentParticipant
  1─1 TournamentRulesSnapshot(payload, content_hash)          ← congelado no lock
  1─* TournamentDeckSubmission(participant, snapshot→DeckSnapshot, content_hash, validation, locked)
  1─* TournamentCheckIn
  1─* TournamentStage(kind) 1─* TournamentRound 1─* TournamentMatch
        TournamentMatch(participant_a/b, winner, state, score_a/b, next_match/slot,
                        loser_next_match/slot, bracket, is_draw)   ← elim/swiss/RR/double
          1─* TournamentGame ; 1─* MatchReport ; 1─* MatchDispute
  1─* TournamentStanding(rank, wins, losses, draws, points, tiebreaks)
  1─* TournamentAuditLog(action, actor, payload)
```

## common
```
AuditLog(action, actor→User, target_type/id, payload, source)   ← cross-cutting append-only
BaseModel = UUID + created_at/updated_at ; SoftDeleteModel = deleted_at
```
