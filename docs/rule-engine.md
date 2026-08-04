# Rule Engine

Motor de validação de decks centralizado no backend (**fonte de verdade**). O
frontend faz validação otimista, mas a palavra final é do backend.

Código: [`apps/validation/engine.py`](../backend/apps/validation/engine.py) +
[`apps/validation/service.py`](../backend/apps/validation/service.py).

## Entrada

`validate_deck_version(version, *, owned_map, power_policy, banlist_version, reference_date)`
monta um `ValidationContext` com:

- **Deck** (linhas: card, zona, quantidade, grade, trigger, nation, tipo).
- **Formato + versão** — `FormatRuleVersion` vigente na `reference_date` (regras no banco).
- **Banlist + versão** — opcional (`?banlist=` no endpoint, ou snapshot do torneio).
- **Política de power level** — opcional (torneio).
- **Data de referência** — para regras/versões temporais.
- **owned_map** — para o aviso de coleção (nunca erro).

## Regras (plugáveis)

Cada regra é uma subclasse de `Rule` com `check(ctx) -> list[issue]`. A lista
`DEFAULT_RULES` define a ordem:

| Regra | Severidade | O que faz |
|-------|-----------|-----------|
| `ZoneCountRule` | erro | Min/max por zona (Main/Ride/G) da `FormatZoneRule`. |
| `CopyLimitRule` | erro | Limite de cópias **por identidade canônica** (`FormatConstructionRule`). |
| `TriggerRule` | erro/aviso | Total de triggers, limite de Over Trigger, limites por tipo. |
| `NationLockRule` | erro | Nation única quando o formato trava. |
| `BanlistRule` | erro | Delega para `apps.banlists.services.banlist_violations` (banido, LIMIT_TO_N, First Vanguard, Choice Restriction, grupos, condicionais). |
| `PowerPolicyRule` | erro | Política do torneio sobre os power levels existentes (máx por carta, faixa, máx acima de N, orçamento). |
| `CollectionWarningRule` | **aviso** | Cópias faltantes na coleção — **jamais** invalida o deck. |

## Saída (formato estável)

```json
{
  "is_valid": false,
  "errors": [{"code": "BANNED_CARD", "card_id": "...", "message": "...", "zone": "...",
              "current_quantity": 1, "allowed_quantity": 0}],
  "warnings": [{"code": "MISSING_OWNED_COPIES", "card_id": "...", "missing_quantity": 3}],
  "summary": {"main_deck_count": 50, "ride_deck_count": 5, "trigger_count": 16,
              "maximum_power_level": 7, "power_point_total": 166},
  "format_rules_version": 1, "banlist_version": 2, "reference_date": "2026-08-04"
}
```

## Separação rígida de categorias

- **Erro de regra** → `errors` (invalida).
- **Aviso de coleção** (cópias faltando) → `warnings` (nunca invalida).
- **Aviso de informação incompleta / dados desatualizados** → `warnings`.

> Garantia testada (`test_04`, `CollectionWarningRule`): usar 4 cópias possuindo 1
> gera `MISSING_OWNED_COPIES` como **warning**, e nenhum erro de posse.

## Estendendo

1. Crie uma subclasse de `Rule`.
2. Adicione-a a `DEFAULT_RULES` (ou passe `rules=` para `run_engine`).
3. Regras de formato/banlist novas entram **no banco** (nova `FormatRuleVersion` /
   `BanlistVersion`) — sem migration de código.

## Nota sobre power level e IA

O cálculo de força do deck (`apps.powerlevel.services.deck_power_stats`) é uma
**estimativa**. O único dado editorial oficial é o power level individual das
cartas, definido por Platform Admins. Nenhuma IA altera power levels; sugestões
de IA (futuro) seriam drafts privados para revisão administrativa — nunca
publicadas automaticamente.
