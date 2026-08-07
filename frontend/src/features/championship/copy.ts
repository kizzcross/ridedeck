/** Plain-language, jargon-free copy for the roster championship. The goal: a
 *  first-time player who has never heard of an "Ace" or a "roster" reads a couple
 *  of friendly sentences and gets it. Keep everything human — no technical terms. */

export const SELECTION_MODE_LABEL: Record<string, string> = {
  manual: "Você escolhe (em segredo)",
  random_free: "Sorteio livre",
  random_no_consecutive: "Sorteio sem repetir seguido",
  random_rotation: "Rodízio dos decks",
  predetermined_order: "Ordem sorteada antes",
  choose_from_random: "Sorteia alguns, você escolhe 1",
};

/** How you get your deck each round — one friendly sentence per mode. */
export const SELECTION_MODE_HELP: Record<string, string> = {
  manual:
    "Antes de cada partida você escolhe qual dos seus decks vai usar, sem o adversário ver. Quando os dois escolhem, as escolhas aparecem ao mesmo tempo.",
  random_free:
    "O sistema sorteia um dos seus decks para cada partida. Pode cair o mesmo deck várias vezes seguidas — é na sorte.",
  random_no_consecutive:
    "O sistema sorteia um dos seus decks, mas nunca o mesmo que você acabou de usar na partida anterior.",
  random_rotation:
    "O sistema sorteia seus decks em rodízio: todos os seus decks precisam aparecer uma vez antes de qualquer um repetir. Assim você usa o time inteiro, não só o mais forte.",
  predetermined_order:
    "A ordem em que seus decks vão aparecer é sorteada uma vez, no começo, e fica valendo até o fim. Ninguém muda depois.",
  choose_from_random:
    "A cada partida o sistema sorteia alguns dos seus decks e você escolhe qual deles usar. Um meio-termo entre sorte e estratégia.",
};

/** What an "Ace" is — for someone who has never seen the term. */
export const ACE_INTRO =
  "O Ace é o seu deck de estimação — o queridinho do seu time. Você marca um dos seus decks como Ace e ele ganha um destaque especial (uma coroa) em todo o campeonato. Dependendo das regras, ele também pode te dar uma pequena vantagem.";

/** Per-rule, what marking an Ace actually does — in plain terms. */
export const ACE_RULE_HELP: Record<string, string> = {
  visual_only:
    "Aqui o Ace é só um destaque visual: mostra qual é o seu deck favorito, sem mudar nada nas partidas.",
  manual_once:
    "Uma vez no campeonato, você pode decidir jogar com o seu Ace em vez do deck que sairia normalmente.",
  replace_draw:
    "Se o sistema sortear um deck que você não quer, uma vez no campeonato você pode trocar aquele sorteio pelo seu Ace.",
  weighted_random:
    "Nos sorteios, o seu Ace tem uma chance um pouco maior de aparecer que os outros decks.",
  extra_in_rotation:
    "No rodízio de decks, o seu Ace pode aparecer uma vez a mais que os demais dentro de cada ciclo.",
  tiebreak_wins:
    "Suas vitórias jogando com o Ace contam como critério de desempate na classificação (não valem pontos a mais).",
};

/** The whole thing, explained as a short story. Used on the first visit. */
export const HOW_IT_WORKS_STEPS: { title: string; body: string }[] = [
  {
    title: "Você monta um time de decks",
    body:
      "Em vez de trazer um deck só, você inscreve vários. Esse conjunto é o seu \"time\" para o campeonato.",
  },
  {
    title: "Cada deck vale pontos de força",
    body:
      "O organizador dá uma nota de força para cada deck. A soma das notas do seu time não pode passar de um limite. Assim ninguém enche o time só de decks fortíssimos.",
  },
  {
    title: "Cada partida usa um deck do time",
    body:
      "Na hora de jogar, você usa apenas um deck. Dependendo do campeonato, você escolhe qual, ou o sistema sorteia para você.",
  },
  {
    title: "O melhor da fila leva",
    body:
      "Você ganha pontos vencendo partidas. No fim, quem tiver mais pontos (ou vencer o mata-mata) é o campeão.",
  },
];

export const ROSTER_HELP =
  "Este é o seu time de decks. Adicione decks até preencher todas as vagas e mantenha a soma de força dentro do limite. A barra no topo mostra quanto de força você já usou.";

export const POWER_HELP =
  "A força de cada deck é definida pelo organizador do campeonato — você não muda esse número. Ele serve só para equilibrar os times.";
