# RideDeck — Design System

Identidade **arcade TCG**: pixel-forward, painéis "chunky" com sombra dura,
âmbar energético sobre índigo profundo. Dark-first, com tema claro completo.
Original — não deriva de nenhum asset da Bushiroad.

Fonte de verdade dos tokens: [`frontend/src/styles/index.css`](../frontend/src/styles/index.css)
(bloco `@theme` do Tailwind v4). Tudo aqui referencia CSS variables — nunca cores hardcoded.

---

## 1. Tipografia

| Papel | Fonte | Uso |
|-------|-------|-----|
| Display / labels | **Silkscreen** | Títulos, botões, badges, nav — sempre `uppercase`, `tracking` largo. Classe `.font-display`. |
| Corpo | **Pixelify Sans** | Texto, inputs, parágrafos. É pixelada mas legível. |

Carregadas via Google Fonts em [`index.html`](../frontend/index.html).

## 2. Cores (tokens semânticos)

Cada token existe em dark (default) e é remapeado em `html.light`.

| Token | Dark | Papel |
|-------|------|-------|
| `--color-canvas` | `#12122a` | Fundo da página (com grid sutil) |
| `--color-surface` | `#1b1b3a` | Painéis |
| `--color-surface-2/3` | `#24244d` / `#2f2f61` | Camadas elevadas |
| `--color-border` | `#0c0c1c` | Contorno chunky (2px) + sombra dura |
| `--color-ink` / `-muted` / `-subtle` | `#f6f4ff` … | Texto |
| `--color-accent` | `#ffcf4a` | Âmbar arcade — ação principal, foco |
| `--color-violet` / `--color-cyan` | `#b07bff` / `#56d7e6` | Apoios |
| `--color-success/warning/danger/info` | verde/âmbar/vermelho/ciano | Estados |

**Grades** têm cor própria (`--color-grade-0..4`): cinza, verde, ciano, violeta, âmbar.

## 3. Formas & elevação

- **Raio**: `--radius-card` = `0.4rem` (cantos discretos, quase retos).
- **Sombra dura**: `--shadow-hard` = `4px 4px 0 0 var(--color-border)` (offset, sem blur — cara de arcade). Versão `-sm` = 2px.
- **Press**: `.rd-press` translada 2px no `:active` (sensação de botão físico).
- **Bordas**: 2px sólidas na cor `--color-border` (bem escura) para o look "outlined".

## 4. Componentes base

[`frontend/src/components/ui/`](../frontend/src/components/ui/)

| Componente | Notas |
|------------|-------|
| `Button` | Variants: primary (âmbar), secondary, ghost, outline, danger. Chunky + `rd-press`. |
| `Panel` / `PanelHeader/Body` | Card com borda 2px + sombra dura. |
| `Badge` | Pill pixelada com borda; tones incl. `official` (violeta) e `community` (ciano). |
| `Input` | Borda 2px, foco âmbar, erro não depende só de cor (ícone ⚠ + `aria-invalid`). |
| `Drawer` | Slide-over acessível (Escape + backdrop), trava scroll. |
| `Toast` | `success/error/info/warning`, `aria-live`, ícone + cor. |
| `Skeleton` | Shimmer para loading. |

## 5. Acessibilidade

- Foco visível de 3px âmbar em tudo interativo.
- Estados de erro nunca dependem só de cor (ícone + texto + `aria`).
- Alvos ≥ 32px; navegação por teclado; `aria-label` em ícones-botão.

---

## 6. 🏳️ Ícones de Nation e Clan

Usa os **emblemas oficiais** de nation e clan, referenciados por URL a partir do
wiki da comunidade (mesma abordagem das artes de carta — hotlink, sem
redistribuir; projeto de fã). Mapa em
[`frontend/src/lib/vanguardIcons.ts`](../frontend/src/lib/vanguardIcons.ts)
(11 nations + 24 clans).

Componentes em [`frontend/src/components/NationLogo.tsx`](../frontend/src/components/NationLogo.tsx):

- `<NationLogo nation={slug} size={n} />` — emblema oficial da nation; **cai para
  um glifo pixel 9×9** se a imagem falhar ao carregar (fallback offline).
- `<NationCoin nation={slug} size={n} />` — emblema sobre um tile (canto das cartas).
- `<ClanIcon clan={"Royal Paladin"} size={n} />` — emblema oficial do clan (G-era).

**Uso na UI**: moeda no canto de cada carta, verso-placeholder, drawer de detalhe
(nation + clan), avatar do usuário e o picker de avatar do perfil.

### Fallback pixel-art (9×9)

Se o emblema oficial não carregar, o `NationLogo` desenha um glifo pixel próprio
(SVG `crispEdges`) na cor da nation — mantém o visual arcade sem depender da rede.
Os bitmaps ficam em `NATION_GLYPHS` no mesmo arquivo.

### Paleta por nation

| Nation | slug | Cor | Era |
|--------|------|-----|-----|
| Dragon Empire | `dragon_empire` | `#ff6b6b` | D + clássica |
| Dark States | `dark_states` | `#b07bff` | D |
| Brandt Gate | `brandt_gate` | `#ffcf4a` | D |
| Keter Sanctuary | `keter_sanctuary` | `#56d7e6` | D |
| Stoicheia | `stoicheia` | `#66e08a` | D |
| Lyrical Monasterio | `lyrical_monasterio` | `#ff9ecb` | D |
| United Sanctuary | `united_sanctuary` | `#ffd25c` | clássica/G |
| Dark Zone | `dark_zone` | `#8a90b8` | clássica/G |
| Magallanica | `magallanica` | `#56d7e6` | clássica/G |
| Zoo | `zoo` | `#66e08a` | clássica/G |
| Star Gate | `star_gate` | `#b07bff` | clássica/G |

### Glifos 9×9 (`#` = pixel aceso)

Cada bitmap é a fonte real usada pelo componente — edite lá pra ajustar o desenho.

**Dragon Empire** (chama)
```
....#....
...##....
...###...
..####...
.#####...
.######..
.##.###..
.##..##..
..####...
```

**Keter Sanctuary** (gema)
```
....#....
...###...
..#####..
.#######.
#########
.#######.
..#####..
...###...
....#....
```

**United Sanctuary** (coroa)
```
#...#...#
#.#.#.#.#
#.#.#.#.#
#.#.#.#.#
#########
.#######.
.#.#.#.#.
.#######.
.........
```

**Star Gate** (estrela)
```
....#....
...###...
...###...
#########
.#######.
#########
...###...
...###...
....#....
```

**Lyrical Monasterio** (coração), **Brandt Gate** (engrenagem), **Dark States** (lua),
**Dark Zone** (morcego), **Magallanica** (ondas), **Stoicheia** (folha) e **Zoo** (pata)
seguem o mesmo formato — ver o arquivo do componente para os bitmaps completos.

### Como adicionar / trocar uma logo

1. Edite o bitmap 9×9 em `NATION_GLYPHS` (`NationLogo.tsx`).
2. Defina a cor em `NATION_COLORS` (`frontend/src/lib/cardMeta.ts`).
3. Se for uma nova nation, adicione o slug em `Nation` (`backend/apps/cards/choices.py`)
   e o label em `NATION_LABELS`.

> **Próximo passo sugerido**: substituir os glifos abstratos por emblemas pixel dedicados
> por nation (arte 16×16 ou 32×32) mantendo o mesmo contrato de componente — nada mais na
> UI precisa mudar.
