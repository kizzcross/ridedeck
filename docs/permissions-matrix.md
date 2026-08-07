# Matriz de permissões

Três conceitos distintos, nunca confundidos:

- **Platform Admin** — papel **global** (`accounts.PlatformRole.PLATFORM_ADMIN` ou superuser).
- **Tournament Organizer** — papel **por-objeto**: criador/staff de um torneio específico.
- **User (Membro)** — usuário autenticado padrão.

Toda decisão de autorização vive no backend (`apps/common/permissions.py` + guards
por-objeto). Flags do cliente **nunca** são confiadas.

| Ação | Platform Admin | Tournament Organizer | User |
|------|:---:|:---:|:---:|
| Criar/editar/publicar decks próprios; like/fav/fork | ✅ | ✅ | ✅ |
| Controlar coleção pessoal | ✅ | ✅ | ✅ |
| Favoritar cartas; escolher avatar; convidar (referral) | ✅ | ✅ | ✅ |
| Amigos + solicitações | ✅ | ✅ | ✅ |
| Criar banlist **comunitária** (+ editar/fork/publicar as suas) | ✅ | ✅ | ✅ |
| Criar torneio (vira **Organizer** daquele torneio) | ✅ | ✅ | ✅ |
| Inscrever-se, submeter deck, check-in, reportar/confirmar/**contestar** resultado | ✅ | ✅ | ✅ |
| Definir o **nível do próprio deck** (1–5 estrelas) | ✅ | ✅ | ✅ |
| Gerir **o próprio** torneio (lock, bracket, aprovar inscrições, DQ, corrigir resultado) | ✅ | ✅ (só o seu) | ❌ |
| Selecionar banlist do torneio | ✅ | ✅ (só o seu) | ❌ |
| **Campeonato**: montar o próprio time (roster) + Ace; escolher/confirmar deck da rodada | ✅ | ✅ | ✅ |
| **Campeonato**: atribuir/editar a **força** dos decks; sortear/re-sortear; penalidades; resolver disputas | ✅ | ✅ (só o seu) | ❌ |
| **Marcar banlist como oficial** | ✅ | ❌ | ❌ |
| Criar versões oficiais de regras de formato | ✅ | ❌ | ❌ |
| Gerenciar sincronização de catálogo / corrigir dados / importar | ✅ | ❌ | ❌ |
| **Promover amigo a Platform Admin** | ✅ | ❌ | ❌ |
| Administrar torneio de **outra** pessoa | ✅ (moderação) | ❌ | ❌ |

## Onde é aplicado

- `IsPlatformAdmin` — banlist oficial (`banlists/{id}/make-official/`),
  sincronização (`admin/imports/*`, `admin/data-sources/*`), promoção de admin
  (`admin/users/promote/`).
- `Tournament.is_organizer(user)` — guard por-objeto em todas as ações de gestão de
  torneio, **inclusive campeonato** (atribuir força, `run-draws`, `apply-penalty`,
  `resolve-dispute`, `rosters`). O jogador só mexe no **próprio** roster/seleção
  (guard por `participant.user == request.user`).
- `IsOwnerOrReadOnly` / checagens de `owner` — decks (inclui `power_stars`) e
  banlists comunitárias.
- Serializers marcam `role`/flags de admin como **read-only** — registro nunca
  auto-eleva. Em campeonato, o serializer de seleção **esconde o deck do adversário**
  até o reveal.

## Cobertura de testes de aceitação

Consolidados em [`apps/common/tests/test_acceptance.py`](../backend/apps/common/tests/test_acceptance.py):

1. Dono **define** o nível do próprio deck (1–5 estrelas). 2. Não-dono **não** muda
o nível do deck de outra pessoa. 3. Nível fora de 1–5 é **rejeitado**. 4. Falta de
cópias **não** invalida deck. 5. Carta banida invalida. 6. LIMIT_TO_1 invalida com
2. 7. Choice Restriction bloqueia incompatíveis. 8. Banlist futura **não** muda
snapshot do torneio. 9. Editar deck original **não** muda submissão. 10. Bracket
**não** avança 2×. 11. Usuário **não** gere torneio alheio. 12. Comunitária **não**
vira oficial por usuário comum.

O **modo campeonato** tem suíte própria em
[`apps/tournaments/tests/test_roster.py`](../backend/apps/tournaments/tests/test_roster.py)
e [`test_selection.py`](../backend/apps/tournaments/tests/test_selection.py)
(cap/validação de roster, atribuição de força só pelo dono, sorteio por modo,
reveal secreto, Ace, penalidades, disputas, visibilidade fechada). — **todos passam.**
