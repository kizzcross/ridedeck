# Modo Campeonato — Roster / Power Cap / Sorteio / Ace

Um tipo de torneio (`Tournament.kind = "roster"`) que **coexiste** com os torneios
clássicos. O conceito: cada jogador inscreve um **time de decks** dentro de um
**limite de força**; a cada rodada usa **um** deck (escolhido ou sorteado); há um
**Ace Deck** opcional. Cada partida de Vanguard continua sendo **1 jogador × 1
deck** — por isso reaproveitamos todo o motor de pareamento/bracket/standings, e o
roster + seleção de deck são uma **camada por cima**.

Código: [`apps/tournaments/roster.py`](../backend/apps/tournaments/roster.py),
[`apps/tournaments/selection.py`](../backend/apps/tournaments/selection.py),
[`apps/tournaments/presets.py`](../backend/apps/tournaments/presets.py) e as telas
em [`frontend/src/features/championship/`](../frontend/src/features/championship/).

---

## 1. Conceito

- **Time de decks**: o jogador inscreve `decks_per_player` decks.
- **Força por deck**: definida **pelo dono do campeonato** (não pelo jogador). A
  soma das forças do time não pode passar de `power_cap`. `min/max_deck_power` são
  opcionais. `Deck.power_stars` (1–5, escolhido pelo dono do deck) entra apenas
  como **sugestão/valor inicial**.
- **Deck por partida**: apenas um; sem ban de deck entre jogadores; nunca vários
  decks no mesmo confronto.

## 2. Entidades

```
Tournament(kind="roster", format_kind, bracket_type, seed_source,
           decks_per_player, power_cap, min/max_deck_power,
           deck_selection_mode, random_options_count, draw_timing,
           sequence_self/opponent_visibility, roster_visibility, reveal_lists_after_end,
           ace_enabled, ace_rule, ace_reveal, ace_required,
           allow_draws, points_win/draw/loss/bye, rounds_count, hybrid_advance_count, …)

TournamentRoster(participant 1─1, status[draft|valid|invalid|confirmed|locked],
                 power_used, is_over_cap, confirmed_at)
  1─* RosterDeck(source_deck→Deck, snapshot→DeckSnapshot, power[dono], power_by,
                 is_ace, banlist_valid, is_valid, label, slot, locked)  uniq(roster, source_deck)
  1─* RosterDeckSequence(round_number, roster_deck, revealed)   ← só predetermined_order (congelado)

MatchDeckSelection(match, participant, roster_deck?, method, confirmed, revealed,
                   is_ace_used, options[], eligible[], rule_used)  uniq(match, participant)
DeckDrawLog(tournament, round, participant, result_deck?, eligible[], options[],
            rule, admin_intervention, admin)   ← imutável, um por sorteio
AceEvent(roster, match?, kind[used|replaced_draw|revealed])
TournamentPenalty(participant, match?, kind, points, reason, issued_by)
```

Reaproveita: `TournamentParticipant/Registration/Staff/CheckIn/Stage/Round/Match/
Standing/AuditLog`, `MatchReport/Dispute`, `decks.DeckSnapshot`, `banlists.*`,
`validation.service.validate_deck_version`.

## 3. Fluxos

**Dono**: criar (wizard/preset) → abrir inscrições → **atribuir força** dos decks
(inline, recalcula o cap na hora) → check-in → **travar** (congela snapshots +
força + sequências) → **iniciar** (gera pareamento + sorteia a 1ª rodada) →
acompanhar (sortear/re-sortear, penalidades, disputas, correções) → encerrar.

**Jogador**: inscrever → **montar time** (adiciona decks até o cap) → escolher
**Ace** (cerimônia) → confirmar → check-in → por rodada: escolher/assistir o
sorteio → confirmar "pronto" → jogar → reportar/confirmar resultado.

## 4. Modos de escolha do deck (`deck_selection_mode`)

| Modo | Comportamento |
|------|---------------|
| `manual` | O jogador escolhe secretamente; revela ao ambos confirmarem. |
| `random_free` | Sorteio uniforme; pode repetir à vontade. |
| `random_no_consecutive` | Sorteio, mas nunca o deck da rodada anterior. |
| `random_rotation` | **Rodízio**: todos os decks aparecem 1× antes de repetir; ao fechar o ciclo, reinicia. |
| `predetermined_order` | Sequência sorteada e **congelada** no início (`RosterDeckSequence`), cíclica. |
| `choose_from_random` | Sorteia `random_options_count` (2–3) e o jogador escolhe 1 (secreto). |

`draw_timing`: `before_pairing` · `after_pairing` · `auto_round_start` · `manual_owner`.
Nos modos automáticos, o deck é sorteado quando a rodada abre (e a cada nova rodada).

### Sorteio server-side + auditoria

O sorteio acontece **no servidor** (`selection.ensure_selection`), é **persistido**
(nunca recomputado no cliente) e grava um `DeckDrawLog` imutável. Um novo sorteio
só ocorre por **intervenção do organizador** (`admin_intervention=True`, registrado).
A seleção é inicializada **uma única vez** — re-execuções idempotentes não re-sorteiam
nem apagam uma escolha manual em andamento.

### Reveal simultâneo (gate no servidor)

`MatchDeckSelection.revealed` só vira `True` quando **os dois lados** confirmaram
(`selection.confirm_selection` → `_maybe_reveal`). O serializer esconde o deck do
adversário até lá; o dono/o próprio jogador sempre veem o seu. Tempo real por
**polling** — sem WebSocket.

## 5. Ace Deck (`ace_enabled` + `ace_rule`)

O Ace **não altera nenhuma regra da partida** — só a estrutura do campeonato.

| `ace_rule` | Efeito |
|------------|--------|
| `visual_only` | Apenas destaque visual (coroa). |
| `manual_once` | O jogador pode jogar o Ace uma vez no campeonato. |
| `replace_draw` | Uma vez, troca um sorteio pelo Ace (`selection.use_ace` → `AceEvent`). |
| `weighted_random` | O Ace tem peso maior nos sorteios. |
| `extra_in_rotation` | O Ace pode aparecer 1× a mais por ciclo na rotação. |
| `tiebreak_wins` | Vitórias com o Ace contam como **desempate** (nunca pontos a mais). |

`ace_reveal`: `public` ou `hidden_until_first_use`. `ace_required` torna a escolha
obrigatória para confirmar o time.

## 6. Formatos & seeding

- `format_kind = points` → Swiss (`bracket_type="swiss"`) ou Round Robin.
- `format_kind = bracket` → eliminação simples/dupla.
- `format_kind = hybrid` → Swiss → **Top Cut** (`hybrid_advance_count` avançam).
- `seed_source`: `random` (embaralha), `manual` (mantém seeds do organizador) ou
  `platform_ranking` (por vitórias em campeonatos finalizados).

Pontuação (configurável): vitória `points_win` (3), empate `points_draw` (1, se
`allow_draws`), derrota `points_loss` (0), bye `points_bye` (3). Penalidades ajustam
os pontos na classificação.

## 7. Estados

- **Torneio** (reutiliza `TournamentStatus`): `draft → registration → locked/
  check_in → running → finished`.
- **Rodada** (`RoundStatus`): `pending → active → completed`.
- **Seleção por (match, participante)**: `awaiting_choice`/`awaiting_draw` →
  `picked/drawn (secreto)` → `awaiting_confirm` → `revealed` → `reported` →
  (`disputed`) → `done`.

## 8. Visibilidade de times (`roster_visibility`)

| Valor | Espectador vê |
|-------|---------------|
| `open` | Decks (nome/força/Ace) do time. |
| `partial` | Idem (a lista completa de cartas nunca é exposta pela API). |
| `closed` | Nada — só o que já foi **usado/revelado** em partida. |

Organizador e o próprio dono sempre veem tudo. `reveal_lists_after_end` libera
tudo após o fim. Endpoint: `GET /tournaments/{uuid}/public-rosters/`.

## 9. Permissões

- **Dono/Staff**: config (antes do início), **atribuir/editar força**, gerar
  rodadas, sortear/re-sortear, corrigir resultados, resolver disputas, penalidades,
  check-in, ver tudo.
- **Jogador (dono do próprio roster)**: montar time + Ace até o lock, confirmar,
  escolher/confirmar deck, reportar/confirmar resultado, contestar.
- **Espectador**: conforme `roster_visibility` e reveals já ocorridos.

## 10. Endpoints principais

Todos sob `TournamentViewSet`/`MatchViewSet` (padrão `@action`):

- `GET presets/` · `GET/POST` tournament (config no write serializer).
- `GET my-roster/` · `POST add-roster-deck/` `{deck}` · `POST remove-roster-deck/`
  `{roster_deck}` · `POST set-ace/` `{roster_deck?}` · `POST confirm-roster/`.
- `GET rosters/` (dono) · `POST set-deck-power/` `{roster_deck, power}` (dono).
- `GET public-rosters/` (gated) · `GET roster-standings/` · `GET roster-rounds/`
  (seleções, com reveal gated).
- `POST run-draws/` `{redraw?}` (dono) · `POST apply-penalty/` · `GET penalties/`.
- Match: `POST pick-deck/` `{roster_deck}` · `POST confirm-selection/` ·
  `POST use-ace/` · `POST report/` · `POST confirm/` · `POST dispute/` ·
  `POST resolve-dispute/` (dono) · `POST set-result/` (dono).

## 11. Presets

| Preset | Config |
|--------|--------|
| **Power Rotation** | 4 decks, cap 15, sem Ace, rodízio, suíço, campeão por pontos. |
| **Ace Challenge** | Ace on (substitui sorteio 1×, desempate por Ace), rodízio, pontos. |
| **Random Two** | Sorteia 2, escolhe 1; Ace opcional. |
| **Full Random** | Sorteio livre com repetição; Ace opcional; casual. |
