# Arquitetura — RideDeck

## Visão geral

Monorepo com dois artefatos independentes (`backend/`, `frontend/`) orquestrados
por Docker Compose. O frontend nunca consome fontes externas diretamente — toda
integração passa pelo backend.

## Backend — domínios (`backend/apps/`)

| App          | Responsabilidade | Fase |
|--------------|------------------|------|
| `common`     | Base models (UUID, timestamps, soft delete), audit log, paginação, exceções, middleware, permissões reutilizáveis | 1 |
| `accounts`   | User (login por e-mail), papéis globais (`PlatformRole`), profile, preferences, auth JWT | 1 |
| `cards`      | Card Identity, Card Printing, Sets, imagens, identificadores externos, grupos de equivalência, legalidade por formato | 2 |
| `imports`    | Adapters de dados (TCGCSV/TCGplayer), batches idempotentes, payload bruto, métricas | 2 |
| `collection` | Coleção pessoal, wishlist, itens de troca | 4 |
| `formats`    | Formatos e **versões de regras** (zonas, triggers, construção, exceções) — no banco | 5 |
| `powerlevel` | Escala, power level por identidade/formato, histórico, políticas de torneio | 5 |
| `banlists`   | Banlist/versões/entradas, restriction groups, choice restriction, condições | 6 |
| `decks`      | Deck, DeckVersion, DeckEntry, likes/favoritos/comentários, forks, snapshots | 3 |
| `validation` | **Rule engine** central — fonte de verdade da validação de decks | 3+ |
| `tournaments`| Torneios, inscrições, submissão+snapshot, stages/rounds/matches, brackets, auditoria | 7-8 |

### Princípios

1. **Permissão no backend.** Nenhuma decisão de autorização depende de flag
   enviada pelo cliente. `apps/common/permissions.py` define `IsPlatformAdmin`,
   `IsOwnerOrReadOnly`, etc. Papéis: `PlatformRole` (global) e Tournament
   Organizer (por-objeto, escopo de um torneio).
2. **Identidade canônica ≠ printing.** Limite de cópias, banlist e power level
   operam sobre a identidade da carta (`Card`), não sobre uma impressão isolada.
3. **Regras versionadas no banco.** Formatos, banlists e power levels têm versões
   com validade temporal — novas regras não exigem migration de código.
4. **Snapshots imutáveis.** Ao submeter um deck a um torneio, congela-se a lista
   (com hash), as regras, a banlist e a política de power level. Mudanças futuras
   nessas fontes globais não alteram torneios já iniciados.
5. **Auditoria.** Alterações sensíveis geram registros (audit log genérico +
   tabelas de histórico específicas, ex.: power level).

## Frontend (`frontend/src/`)

| Pasta         | Conteúdo |
|---------------|----------|
| `app/`        | Router, providers (Query, Theme, Toast), ProtectedRoute, AppShell |
| `pages/`      | Páginas de rota |
| `features/`   | Módulos de domínio (deck builder, catálogo…) — crescem por fase |
| `components/ui/` | Design system (Button, Input, Panel, Badge, Toast, Skeleton) |
| `lib/`        | Cliente axios com refresh transparente, tokens, `cn()` |
| `api/`        | Funções tipadas por domínio + tipos |
| `hooks/`      | Estado global (Zustand) — ex.: `useAuth` |

### Autenticação

JWT (access + refresh via SimpleJWT com rotação e blacklist). O cliente axios
injeta o access token e, em `401`, tenta refresh transparente uma vez; se falhar,
dispara `rd:logout` e o estado de auth reage. (Hardening futuro: mover refresh
para cookie httpOnly — desenhado para trocar apenas `lib/tokens.ts`.)

## Fluxo de dados de importação (Fase 2)

```
DataSource ─▶ Adapter (fetch_sets/products/prices/images)
           ─▶ ImportBatch (upsert idempotente por id externo)
           ─▶ RawImportPayload (payload bruto, auditável)
           ─▶ Card / CardPrinting / CardPriceHistory
```

Celery para execução assíncrona, com retry+backoff, rate limit, cache Redis e
métricas por batch. Scraping (se necessário) fica em adapter isolado respeitando
robots.txt/ToS — nunca misturado aos models ou à lógica de decks.
