# Roadmap por fases

| Fase | Escopo | Status |
|------|--------|--------|
| **1** | Fundação: monorepo, Docker Compose, Django+DRF, Vite+React, auth JWT + papéis, design system, models base, migrations, testes | ✅ **Concluída** |
| **2** | Catálogo (Card/Printing/Set), adapters de import (fixture + TCGCSV), busca (trigram), tela de catálogo + detalhe | ✅ **Concluída** |
| **3** | Decks, DeckVersion/Entry, deck builder (dnd-kit), validação básica, publicação, forks | ✅ **Concluída** |
| **4** | Coleção: owned/missing, lista de compras, preço | ✅ **Concluída** |
| **5** | Formatos + rule engine + power levels* + admin UI + audit log **+ deploy** | ✅ **Concluída** (*power level editorial removido na v2.0 — ver Fase 10) |
| **6** | Banlists: restriction groups, choice restriction, comunitárias, versionamento | ✅ **Concluída** |
| **7** | Torneios: inscrições, submissão+snapshot, single elimination, match reporting | ✅ **Concluída** |
| **8** | Swiss/Top Cut/Double elim, standings, desempates, disputas, brackets interativos | ✅ **Concluída** |
| **9** | Performance, testes, acessibilidade, segurança, documentação final | ✅ **Concluída** |
| **10** (v2.0) | **Nível de deck por estrelas** (remoção do power editorial de cartas) + **modo campeonato por roster**: cap de força, 6 modos de sorteio, Ace, pontos/mata-mata/híbrido, painel do organizador, transparência/auditoria, overlay, wizard e explicações em linguagem natural | ✅ **Concluída** |

Ao fim de cada fase: migrations aplicadas, testes rodando, lista do que foi feito
e das limitações, README + docs + CHANGELOG atualizados.

> **v2.0** está detalhada em [`roster-championship.md`](roster-championship.md) e no
> [`CHANGELOG.md`](../CHANGELOG.md).
