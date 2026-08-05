export type RestrictionTone = "danger" | "warning" | "official" | "neutral";

/** Card-level restriction metadata: label, color, and a plain explanation. */
export const RESTRICTION_META: Record<string, { label: string; tone: RestrictionTone; desc: string }> = {
  banned: {
    label: "Banida",
    tone: "danger",
    desc: "Não pode ser incluída no deck de jeito nenhum.",
  },
  limit_to_1: {
    label: "Limite 1",
    tone: "warning",
    desc: "No máximo 1 cópia no deck.",
  },
  limit_to_2: {
    label: "Limite 2",
    tone: "warning",
    desc: "No máximo 2 cópias no deck.",
  },
  first_vanguard_forbidden: {
    label: "Vanguarda inicial proibida",
    tone: "official",
    desc: "Não pode ser usada como Vanguarda inicial (a unidade grade 0 que você coloca virada pra baixo pra começar o jogo). Continua liberada no resto do deck.",
  },
};

export const CARD_RESTRICTIONS = ["banned", "limit_to_1", "limit_to_2", "first_vanguard_forbidden"];

export const GROUP_KINDS: Record<string, { label: string; desc: (n: number) => string }> = {
  choice: {
    label: "Escolha 1",
    desc: () => "Você só pode incluir 1 destas cartas no deck — escolha uma delas.",
  },
  max_distinct: {
    label: "Máx. distintas",
    desc: (n) => `No máximo ${n} carta(s) diferente(s) deste grupo no deck.`,
  },
  max_total: {
    label: "Máx. cópias",
    desc: (n) => `No máximo ${n} cópia(s) somando todas as cartas do grupo.`,
  },
};
