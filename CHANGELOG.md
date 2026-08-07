# Changelog

Todas as mudanças relevantes deste projeto são documentadas aqui.
Formato baseado em [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/);
versionamento aproximadamente [SemVer](https://semver.org/lang/pt-BR/).

---

## [2.1.0] — 2026-08-07

### ✨ Adicionado

- **Importar deck e banlist por lista de texto**, com **match fuzzy** (tolera
  typos) via trigram (`pg_trgm`) sobre o catálogo real. Núcleo reutilizável em
  [`apps/cards/importer.py`](backend/apps/cards/importer.py) +
  [`apps/banlists/importer.py`](backend/apps/banlists/importer.py).
  - **Vários formatos** aceitos: `4x Nome`, `4 Nome`, `Nome x4`, `Nome (4)`, só o
    nome, CSV/TSV, número da carta (`Nome (BT01/001)`) e **cabeçalhos de zona**
    (Main/Ride/G). Na banlist o número é o **limite** (`0`=banida, `1`/`2`=limite)
    + cabeçalhos (Banidas/Limite 1) e inline (`Nome — banida`).
  - **Prévia interativa** (`ImportListModal`): mostra o que foi reconhecido,
    marca typos corrigidos e o que não achou, e deixa **trocar a variante** da
    carta por um dropdown antes de aplicar (adicionar ou substituir).
  - Endpoints: `POST /decks/import-preview/` + `/decks/{uuid}/import-list/`;
    `POST /banlists/import-preview/` + `/banlists/{uuid}/import-list/`.

## [2.0.0] — 2026-08-07

Grande virada no conceito de "força" das cartas/decks e um **novo modo de
campeonato** completo baseado em roster (time de decks), cap de poder, sorteio de
deck por rodada e Ace Deck opcional.

### ⚠️ Breaking changes

- **Removido o power level editorial das cartas.** O antigo app `apps.powerlevel`
  (rating 1–10 por carta/formato, definido por Platform Admins, com histórico e
  auditoria) foi **descontinuado**: modelos, endpoints, painel admin e a regra de
  validação `PowerPolicyRule` deixaram de existir. Uma migração dropa as tabelas.
  - O campo **`Card.power`** (poder de batalha da carta, ex.: 10000) **permanece
    intacto** — é outra coisa, não o rating editorial.
  - `Tournament.power_policy` e a política de power por carta foram removidos.
  - Frontend: removidos `api/powerlevel.ts`, a página `PowerLevelAdminPage` e as
    rotas/nav de administração de power.
- **`validate_deck_version(...)`** não aceita mais `power_policy`; o `summary` da
  validação não retorna mais `maximum_power_level`/`power_point_total`.

### ✨ Adicionado

- **Nível do deck por estrelas (1–5).** Novo campo `Deck.power_stars`, escolhido
  pelo **dono do deck** no builder por um seletor de estrelas pixeladas. Serve de
  sugestão de força e é reaproveitado nos campeonatos.
- **Modo Campeonato (roster / power cap / sorteio / Ace)** — `Tournament.kind =
  "roster"`, coexistindo com os torneios clássicos:
  - **Time de decks** por jogador (`TournamentRoster` + `RosterDeck`), com **cap
    total de poder** definido pelo campeonato; a **força de cada deck é atribuída
    pelo dono do torneio** (não pelo jogador), com mín./máx. opcionais.
  - **6 modos de escolha do deck por rodada**: manual secreto, aleatório livre,
    aleatório sem repetir seguido, **rodízio** (todos antes de repetir), ordem
    sorteada pré-definida (congelada) e "sorteia N, você escolhe 1".
  - **Momento do sorteio** configurável (antes/depois do pareamento, automático no
    início da rodada, ou manual pelo dono).
  - **Reveal simultâneo**: o deck do adversário fica oculto até os dois
    confirmarem — travado no servidor (`MatchDeckSelection.revealed`).
  - **Ace Deck opcional** com regras: só visual, jogar/substituir sorteio 1×, peso
    maior no sorteio, aparição extra na rotação, ou desempate por vitórias com Ace.
    Nunca vale pontos a mais.
  - **Formatos**: só pontos (suíço / todos-contra-todos), só mata-mata (simples/
    dupla) ou **híbrido** (pontos → top-cut), com **seeding** por sorteio, manual
    ou ranking da plataforma.
  - **Classificação rica**: pontos, vitórias/derrotas, **taxa de vitória por
    deck**, vitórias com Ace e **penalidades** (com desempate configurável).
  - **Visibilidade de times**: aberto / parcial / fechado (esconde o deck do
    adversário até ser usado); opção de revelar listas após o fim.
  - **Painel do organizador**: edição **inline e rápida** da força dos decks de
    todos os times, gerar rodada, sortear/re-sortear (intervenção registrada),
    penalidades e resolução de disputas.
  - **Auditoria de sorteio**: cada sorteio grava um `DeckDrawLog` imutável
    (data/hora, elegíveis, resultado, regra, rodada, intervenção admin).
  - **Presets** de 1 clique: Power Rotation, Ace Challenge, Random Two, Full Random.
- **Experiência visual premium** para o campeonato:
  - Componentes: `DeckCard`, `CapMeter` (nunca depende só de cor), `PowerBadge`,
    `AceSeal`, `VersusBoard`, `AceCeremony`, `DrawAnimator`, `RosterStandings`,
    `TournamentWizard`, `OwnerControlPanel`, `Explainer`.
  - **Cerimônia do Ace** (tela cheia com brilho/partículas) e **animação de
    sorteio** (embaralha → revela).
  - **Explicações em linguagem natural**, sem jargão e **dispensáveis** ("Entendi,
    não mostrar de novo") em todas as telas do campeonato.
  - `framer-motion` + `MotionProvider` respeitando `prefers-reduced-motion` e um
    **botão de reduzir animações** no cabeçalho.
- **Overlay de transmissão** (`/overlay/:uuid`) sem menus, para OBS — nunca vaza o
  deck do adversário.
- **Wizard de criação** multi-etapas com preview ao vivo e presets.

### 🔧 Alterado

- `lock_registration` agora congela os rosters (snapshots + poder) em modo
  campeonato, reaproveitando `DeckSnapshot`.
- Reaproveitamento do motor de pareamento/bracket/Swiss/standings existente — cada
  partida continua 1 jogador × 1 deck; roster e seleção de deck são uma camada por
  cima.
- Criação de torneios: "Torneio rápido" (bracket clássico) vs. **"Novo
  campeonato"** (wizard). Cards de campeonato ganham selo "Campeonato".
- **Performance**: rotas pesadas (builder, campeonato, animações) agora com
  **code-splitting** (lazy load) — bundle principal mais enxuto.

### 🐛 Corrigido

- Sorteio idempotente: uma escolha manual ainda não confirmada não é mais apagada
  quando outra partida da rodada é finalizada (a seleção é inicializada uma única
  vez; re-sorteio só por intervenção do organizador).

### 🧪 Qualidade

- **105 testes de backend** (Django/pytest) verdes, incluindo cobertura do modo
  campeonato: cap/validação de roster, atribuição de poder, cada modo de sorteio,
  rotação sem repetir até fechar o ciclo, reveal secreto (gate de servidor),
  `DeckDrawLog` imutável, Ace (uso único, desempate), penalidades, disputas,
  visibilidade fechada e geração de bracket em modo roster.
- `ruff` limpo, `tsc` limpo, build de produção sem avisos de tamanho, testes de
  frontend verdes, `makemigrations --check` sem pendências.

### 📚 Docs

- Novo [`docs/roster-championship.md`](docs/roster-championship.md).
- Atualizados: `architecture`, `erd`, `permissions-matrix`, `rule-engine`,
  `snapshots`, `design-system`, `decisions-and-risks`, `roadmap` e o `README`.

---

## [1.0.0] — Fases 1–9

Plataforma base RideDeck (ver [`docs/roadmap.md`](docs/roadmap.md)):

- **Fundação**: monorepo Django + React/Vite, Docker Compose, auth JWT + papéis,
  design system arcade, models base.
- **Catálogo** de cartas (identidade canônica ≠ printing), adapters de importação,
  busca por trigram.
- **Deck builder** interativo (dnd-kit), validação básica, publicação, forks.
- **Coleção** pessoal (owned/missing, lista de compras, preços).
- **Formatos + rule engine** versionados no banco + (à época) power level editorial
  + audit log + deploy.
- **Banlists** (oficiais e comunitárias) com restriction groups, choice restriction
  e versionamento.
- **Torneios**: inscrições, submissão + snapshot imutável, single/double
  elimination, Swiss, Swiss + Top Cut, round robin, standings, desempates,
  disputas e brackets interativos.
