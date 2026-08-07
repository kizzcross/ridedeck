# Sistema de Snapshots

Snapshots congelam dados globais mutáveis em um ponto no tempo, para que
mudanças futuras **nunca** alterem retroativamente algo já decidido.

## Onde há snapshot

| Snapshot | Modelo | Quando é criado | Congela |
|----------|--------|-----------------|---------|
| Regras do torneio | `TournamentRulesSnapshot` | No **lock** das inscrições | Versão das regras de formato, banlist + versão, custom rules, Bo-N — com `content_hash`. |
| Deck submetido (clássico) | `TournamentDeckSubmission` + `DeckSnapshot` | Na **submissão** | Lista exata de cartas (por identidade + zona + qtd), com `content_hash`, e o resultado da validação daquele momento. |
| **Deck do roster** (campeonato) | `RosterDeck.snapshot` → `DeckSnapshot` | No **lock** dos rosters | Lista de cada deck do time **+ a nota de força** atribuída pelo dono; o roster fica `locked`. |
| Sequência de sorteio | `RosterDeckSequence` | No lock (modo `predetermined_order`) | A ordem em que os decks vão aparecer, cíclica — imutável. |
| Deck (genérico) | `DeckSnapshot` | Sob demanda (`/decks/{id}/snapshot/`) | Entradas do deck + hash. |
| Banlist | `BanlistVersion` | A cada versão publicada | Entradas + grupos de restrição. |
| Sorteio de deck | `DeckDrawLog` | A cada sorteio | Elegíveis, resultado, regra, rodada, intervenção admin — **append-only, nunca editado**. |

## Hash de conteúdo

`content_hash = sha256(json(entries, sort_keys))`. Duas submissões idênticas
produzem o mesmo hash; qualquer diferença muda o hash. Usado para detectar
adulteração e comparar listas.

## Garantias (testadas)

- **`test_08`** — Banir uma carta na banlist global **depois** da submissão não
  altera `content_hash` nem a `validation` armazenada da submissão.
- **`test_09`** — Editar o deck original **depois** de submeter não muda o
  `payload` congelado da submissão (o snapshot copia as entradas).

## Fluxo no torneio

```
inscrições abertas → jogadores submetem deck  ┐ (cada submissão = DeckSnapshot + hash)
                                              │
organizador trava → TournamentRulesSnapshot   │  congela regras/banlist/power
                    submissões marcadas locked ┘  (deck original continua editável fora do torneio)
                    ↓
check-in → seeding → bracket → resultados
```

Uma mudança futura na banlist global ou nas regras de formato não afeta um torneio
já travado — ele usa seus próprios snapshots. No **modo campeonato**, editar ou
apagar um deck de origem depois do lock também não muda o time: cada `RosterDeck`
usa seu `DeckSnapshot` congelado e a força atribuída pelo dono.
