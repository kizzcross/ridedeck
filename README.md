# RideDeck — plataforma competitiva de Cardfight!! Vanguard

Plataforma web completa: catálogo de cartas, deck builder interativo, controle de
coleção, publicação de decks, **nível de deck por estrelas**, banlists (oficiais e
da comunidade), torneios com brackets, **modo campeonato por roster** (time de
decks + cap de força + sorteio + Ace) e validação automática de decks.

> Projeto de fã, **não afiliado à Bushiroad**. Em ambiente de desenvolvimento os
> dados de cartas são fictícios/placeholder.

## Stack

| Camada        | Tecnologias |
|---------------|-------------|
| Backend       | Python 3.13, Django 5, DRF, SimpleJWT, django-filter, drf-spectacular, Celery, Redis, PostgreSQL 16 |
| Frontend      | React 18, TypeScript, Vite, Tailwind v4, TanStack Query, React Router, React Hook Form, Zod, dnd-kit |
| Infra         | Docker Compose (backend, frontend, postgres, redis, celery-worker, celery-beat) |

## Arquitetura em 30 segundos

```
frontend (Vite/React)  ──HTTP/JSON──▶  backend (Django/DRF)  ──▶  PostgreSQL
        │                                     │
        └── proxy /api ──────────────────────┘        Celery worker+beat ──▶ Redis
```

- Backend organizado por **domínios** em `backend/apps/*` (bounded contexts).
- Permissões **sempre** no backend — nunca confiando em flags do frontend.
- Regras de formato e banlist ficam **no banco** e são **versionadas**.
- Torneios guardam **snapshots imutáveis** (regras, banlist, deck/roster submetido).

### Documentação

| Doc | Conteúdo |
|-----|----------|
| [architecture.md](docs/architecture.md) | Arquitetura, apps por domínio, princípios |
| [erd.md](docs/erd.md) | Diagrama textual de todas as entidades |
| [permissions-matrix.md](docs/permissions-matrix.md) | Matriz de permissões + 12 testes de aceitação |
| [rule-engine.md](docs/rule-engine.md) | Motor de validação de decks (regras plugáveis) |
| [snapshots.md](docs/snapshots.md) | Sistema de snapshots imutáveis + hash |
| [design-system.md](docs/design-system.md) | Design system arcade + motion + ícones de nation/clan |
| [roster-championship.md](docs/roster-championship.md) | **Modo campeonato** (roster, cap, sorteio, Ace) — entidades, fluxos, endpoints |
| [decisions-and-risks.md](docs/decisions-and-risks.md) | Decisões técnicas, riscos e próximos passos |
| [roadmap.md](docs/roadmap.md) | Status das fases |
| [CHANGELOG.md](CHANGELOG.md) | Histórico de mudanças (v2.0) |
| [deploy/DEPLOY.md](deploy/DEPLOY.md) | Deploy no VPS (vanguard.kizzcross.com.br) |

## Subir tudo com Docker (recomendado)

Pré-requisitos: Docker + Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Serviços:

| Serviço  | URL |
|----------|-----|
| Frontend | http://localhost:5173 |
| API      | http://localhost:8000/api/v1/ |
| Docs API (Swagger) | http://localhost:8000/api/docs/ |
| Admin Django | http://localhost:8000/admin/ |

O backend aplica migrations e, se `DJANGO_SEED_ON_START=true`, roda os seeds
automaticamente no primeiro boot.

### Usuários de seed (dev)

| Papel               | E-mail                   | Senha             |
|---------------------|--------------------------|-------------------|
| Platform Admin      | admin@ridedeck.test      | adminpass123      |
| Tournament Organizer| organizer@ridedeck.test  | organizerpass123  |
| Membro              | player@ridedeck.test     | playerpass123     |

## Rodar localmente sem Docker

Você precisa de PostgreSQL e Redis acessíveis (pode subir só esses via Docker:
`docker compose up -d postgres redis`).

### Backend

```bash
cd backend
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
export POSTGRES_HOST=localhost
python manage.py migrate
python manage.py seed_dev
python manage.py runserver
```

### Frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173
```

O `Makefile` na raiz encapsula os comandos comuns: `make up`, `make migrate`,
`make test`, `make seed`, `make createadmin EMAIL=voce@ex.com`, `make schema`.

## Criar um Platform Admin

```bash
cd backend && source .venv/bin/activate
python manage.py create_platform_admin voce@exemplo.com --username voce
# (cria se não existir, promove se já existir)
```

Somente Platform Admins podem publicar banlists oficiais e alterar regras de
formato. (A força dos decks em um **campeonato** é definida pelo **dono daquele
torneio**, não por um Platform Admin — ver
[roster-championship.md](docs/roster-championship.md).)

## Testes

```bash
# backend
cd backend && source .venv/bin/activate && pytest -q
# frontend
cd frontend && npm test
```

## OpenAPI

```bash
cd backend && source .venv/bin/activate
python manage.py spectacular --file schema.yml
```

Ou acesse `http://localhost:8000/api/docs/` com o backend no ar.

## Importar cartas

O frontend **nunca** consome a fonte externa direto — o backend importa e
armazena localmente via camada de *adapters* (`backend/apps/imports/adapters/`).

- **Offline / dev (padrão):** o adapter `fixture` gera 3 sets e 30 cartas
  fictícias. Já roda no `seed_dev`. Para rodar manualmente:
  ```bash
  python manage.py shell -c "from apps.imports.services import ImportRunner, ensure_source; r=ImportRunner(ensure_source('fixture','Fixture')); r.import_sets(); print(r.import_cards().metrics)"
  ```
- **Catálogo real completo (G + D, sem série V)** via management command:
  ```bash
  python manage.py import_catalog --source tcgcsv --series G,D --drop-fixture
  ```
  Puxa ~160 sets → **~15.5k cartas / ~17k printings** com arte (CDN TCGplayer).
  Leva alguns minutos (rate-limited). Idempotente: rodar de novo só atualiza.
  Use `--series G,D,V` para incluir a série V, ou `--set <groupId>` para um set só.

- **Nation / Clan / Trigger (enriquecimento):** a TCGplayer não traz Nation/Clan
  nem o subtipo de trigger. Um adapter isolado (`apps/imports/adapters/fandom.py`)
  preenche esses campos a partir da API pública do wiki Fandom (via *category
  membership*, não scraping de HTML), casando por nome-base. Rode **após** o import:
  ```bash
  python manage.py enrich_clans      # Nation + Clan + Trigger (Critical/Draw/Heal/Front/Stand/Over)
  python manage.py backfill_g_format # marca cartas G-era como legais no formato "G Era"
  ```
  Cobre ~11k cartas com Nation, ~4.6k com Clan e os triggers reais (heal/over não
  aparecem no texto, por isso vêm do wiki).

- **TCGCSV/TCGplayer:** via API admin (autenticado como Platform Admin):
  ```
  POST /api/v1/admin/data-sources/   { "key": "tcgcsv", "name": "TCGCSV", "base_url": "https://tcgcsv.com", "config": {"category_id": "57"} }
  POST /api/v1/admin/imports/trigger/  { "source_key": "tcgcsv", "kind": "full" }   # ou "sets"/"products"/"prices", run_async:true p/ Celery
  ```
- Monitore batches em `GET /api/v1/admin/imports/` (métricas, status, payload bruto).
- Importações são **idempotentes**: rodar de novo atualiza, não duplica.

## Deck Builder (Fase 3)

O deck builder (`/app/decks`) é o centro da experiência:

- Painel de busca de cartas (filtro por grade), **drag-and-drop** com dnd-kit **e**
  clique para adicionar — tudo acessível por teclado.
- Zonas **Main / Ride / G**, controles de quantidade `− n +`, remover.
- **Autosave** por alteração (cada mudança persiste), **undo/redo** (Ctrl+Z / Ctrl+Shift+Z).
- Estatísticas ao vivo (curva de grade, total, triggers) e **validação em tempo real**
  (contagem por zona, limite de 4 cópias por identidade, banlist). O dono do deck
  também define o **nível do deck (1–5 estrelas)** — usado como sugestão de força
  nos campeonatos.
- **Importar por lista de texto** (botão *Importar*): aceita vários formatos
  (`4x Nome`, `Nome x4`, número da carta, CSV, cabeçalhos de zona…) e faz **match
  fuzzy** que corrige typos, com prévia pra revisar antes de aplicar. O mesmo vale
  para **banlists**.
- Visibilidade **private / unlisted / public**, publicação e **fork** (cópia com auditoria).
- **Snapshot** imutável com hash (base para submissão em torneios na Fase 7).

Endpoints: `/api/v1/decks/`, `/decks/{uuid}/entry|validate|publish|fork|snapshot|like|favorite`.

## Coleção (Fase 4)

- Ownership por **printing** (quantidade, condição, idioma, acabamento, preço pago),
  agregado por **identidade** da carta. Wishlist + itens para troca.
- Adicione cartas pela drawer do catálogo (controle **Na coleção**); veja tudo em `/app/collection`.
- **Regra de ouro:** a coleção **nunca invalida** um deck. No builder cada entry mostra
  "⚠ faltam N", e o painel de Coleção traz **% possuído**, lista de compras e estimativa
  de preço das faltantes — tudo como *indicador*, nunca erro de validação.

Endpoints: `/api/v1/collection/`, `/collection/set|owned-map|summary/`, `/wishlist/`, `/trade/`,
`/decks/{uuid}/collection-report/`.

## Modo Campeonato (roster / cap / sorteio / Ace)

Um tipo de torneio (`kind="roster"`) que coexiste com os brackets clássicos. Cada
jogador inscreve um **time de decks** dentro de um **limite de força** (definido
pelo dono do torneio); a cada rodada usa **um** deck (escolhido ou sorteado), com
**Ace Deck** opcional. Cada partida continua 1 deck vs 1 deck — o roster só decide
*quais* decks o jogador pode usar.

- Criação por **wizard** com presets (Power Rotation, Ace Challenge, Random Two,
  Full Random) e explicações em **linguagem natural** dispensáveis.
- 6 modos de sorteio (rodízio, sem repetir seguido, livre, ordem fixa, escolhe-1-de-N,
  manual secreto) com **reveal simultâneo** e sorteio **auditado** (`DeckDrawLog`).
- Pontos / mata-mata / **híbrido**; classificação com taxa por deck, vitórias com
  Ace e penalidades; **painel do organizador** (força inline, sorteios, disputas).
- **Overlay de transmissão** (`/overlay/:uuid`), cerimônia do Ace, animação de
  sorteio, e **reduzir animações** (`prefers-reduced-motion`).

Detalhes completos: [`docs/roster-championship.md`](docs/roster-championship.md).

## PWA (instalável + offline)

O frontend é um **Progressive Web App** (via `vite-plugin-pwa`):

- **Instalável** (Android/iOS/desktop) — manifest com ícones 192/512 + maskable,
  `display: standalone`, tema `#12122a`.
- **Service worker** (autoUpdate) que faz precache do app shell e **runtime cache**:
  artes de carta (TCGplayer, CacheFirst), emblemas de nation/clan (wiki), Google Fonts,
  e leituras de API (NetworkFirst com fallback offline curto).
- Gerado no `npm run build`; em produção o Django serve `/sw.js` e `/manifest.webmanifest`
  via WhiteNoise (same-origin), então a instalação funciona direto em `vanguard.kizzcross.com.br`.
- Ícones em `frontend/public/` (regeráveis; ver `pwa-*.png`).

Testar localmente: `npm run build && npm run preview` e abrir no navegador (o SW só
roda em build, não em `npm run dev`).

## Roadmap por fases

Ver [`docs/roadmap.md`](docs/roadmap.md). A **Fase 1 (fundação)** está concluída:
monorepo, Docker Compose, auth JWT + papéis, design system, models base,
migrations e testes passando.
