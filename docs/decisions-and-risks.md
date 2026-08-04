# Decisões técnicas · Riscos · Próximos passos

## Decisões técnicas

1. **Monorepo standalone** (backend Django + frontend Vite) em vez de embutir no
   pokefit — a stack obrigatória (Vite, Postgres, drf-spectacular, auth própria)
   diverge do pokefit (webpack). Pokefit serviu de referência visual.
2. **Identidade canônica ≠ printing** desde o modelo — limite de cópias, banlist
   e power level operam sobre `Card`, não `CardPrinting`.
3. **Regras no banco e versionadas** (`FormatRuleVersion`, `BanlistVersion`,
   `CardPowerLevel`) — novas regras sem migration de código.
4. **Rule engine plugável** como fonte única de verdade; front só valida otimista.
5. **Snapshots + hash** para imutabilidade de torneios; separação rígida
   erro/aviso (coleção nunca invalida deck).
6. **Papéis**: global (`PlatformRole`) vs por-objeto (Tournament Organizer) —
   nunca confiando em flag do cliente.
7. **Import por adapters** desacoplados; catálogo real vem do TCGCSV/TCGplayer,
   Nation/Clan enriquecidos via API do wiki (hotlink, como as artes) — nunca
   scraping de HTML, respeitando rate limit/ToS.
8. **Deploy** espelha o pokefit no mesmo VPS Hetzner; Django serve o SPA em
   produção (WhiteNoise + catch-all). **PWA** instalável.
9. **JWT** (SimpleJWT, refresh rotativo + blacklist) com refresh transparente no
   axios; desenhado para migrar para cookie httpOnly trocando só `lib/tokens.ts`.

## Riscos / limitações conhecidas

- **Dados da fonte comercial** (TCGplayer): não trazem Nation/Clan nem subtipo de
  trigger — enriquecemos Nation/Clan pelo wiki (~73%/30%), mas ~4k cartas ficam
  sem Nation e triggers reais ficam parciais. Um segundo adapter (banco oficial
  VG) resolveria, respeitando ToS.
- **Double elimination**: roteamento de perdedores é uma implementação
  funcional/simplificada (correta para campos potência-de-2); standings do DE por
  profundidade são aproximados. Swiss/RR/Top Cut são completos.
- **Ícones de nation/clan**: hotlink do CDN do wiki — se o host mudar, o fallback
  pixel-art entra automaticamente.
- **Tempo real** nos brackets é por **polling** (8s), não WebSocket.
- **Sanitização**: comentários/descrições são texto puro e o React escapa por
  padrão (sem `dangerouslySetInnerHTML`) — sem markdown renderizado, sem XSS.
- **Deploy não executado** pelo assistente (sem acesso SSH) — config + passos
  prontos em `deploy/DEPLOY.md`.

## Próximos passos sugeridos

- WebSocket/SSE para brackets em tempo real.
- Segundo adapter (banco oficial VG) para Nation/Clan/trigger 100%.
- Sugestões de power level por IA (drafts privados, nunca auto-publicadas).
- Editor de política de power level e de custom rules de torneio na UI.
- Emblemas pixel dedicados por nation (16×16/32×32) mantendo o contrato do componente.
- CI/CD (workflow SSH) espelhando o do pokefit.
- Full-text search (FTS) além do trigram para busca por habilidade.
