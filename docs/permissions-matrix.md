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
| Inscrever-se, submeter deck, check-in, reportar/confirmar resultado | ✅ | ✅ | ✅ |
| Gerir **o próprio** torneio (lock, bracket, aprovar inscrições, DQ, corrigir resultado) | ✅ | ✅ (só o seu) | ❌ |
| Selecionar banlist + política de power level do torneio | ✅ | ✅ (só o seu) | ❌ |
| **Definir/editar/remover power level** (individual ou em lote) | ✅ | ❌ | ❌ |
| Publicar avaliação de power level como oficial | ✅ | ❌ | ❌ |
| **Marcar banlist como oficial** | ✅ | ❌ | ❌ |
| Criar versões oficiais de regras de formato | ✅ | ❌ | ❌ |
| Gerenciar sincronização de catálogo / corrigir dados / importar | ✅ | ❌ | ❌ |
| **Promover amigo a Platform Admin** | ✅ | ❌ | ❌ |
| Administrar torneio de **outra** pessoa | ✅ (moderação) | ❌ | ❌ |

## Onde é aplicado

- `IsPlatformAdmin` — power level (`admin/power-levels/*`), banlist oficial
  (`banlists/{id}/make-official/`), sincronização (`admin/imports/*`,
  `admin/data-sources/*`), promoção de admin (`admin/users/promote/`).
- `Tournament.is_organizer(user)` — guard por-objeto em todas as ações de gestão
  de torneio (organizer OU staff OU platform admin).
- `IsOwnerOrReadOnly` / checagens de `owner` — decks e banlists comunitárias.
- Serializers marcam `role`/flags de admin como **read-only** — registro nunca
  auto-eleva.

## Cobertura de testes (os 12 mandatórios)

Consolidados em [`apps/common/tests/test_acceptance.py`](../backend/apps/common/tests/test_acceptance.py):

1. Membro **não** edita power level. 2. Organizer **não** edita power level.
3. Admin edita **com justificativa**. 4. Falta de cópias **não** invalida deck.
5. Carta banida invalida. 6. LIMIT_TO_1 invalida com 2. 7. Choice Restriction
bloqueia incompatíveis. 8. Banlist futura **não** muda snapshot do torneio.
9. Editar deck original **não** muda submissão. 10. Bracket **não** avança 2×.
11. Usuário **não** gere torneio alheio. 12. Comunitária **não** vira oficial por
usuário comum. — **todos passam.**
