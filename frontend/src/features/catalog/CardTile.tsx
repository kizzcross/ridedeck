import type { CardListItem } from "@/api/cards";
import { CardArt } from "./CardArt";
import { FavoriteButton } from "./FavoriteButton";
import { NATION_COLORS, nationLabel } from "@/lib/cardMeta";

export function CardTile({ card, onOpen }: { card: CardListItem; onOpen: (c: CardListItem) => void }) {
  const glow = NATION_COLORS[card.nation];
  return (
    <div className="group relative flex flex-col" style={glow ? ({ ["--glow" as string]: `${glow}aa` }) : undefined}>
      <div className="absolute right-1.5 top-1.5 z-20 opacity-0 transition-opacity group-hover:opacity-100 group-focus-within:opacity-100">
        <FavoriteButton cardUuid={card.uuid} size="sm" />
      </div>
      <button
        onClick={() => onOpen(card)}
        className="rd-card flex flex-col rounded-[var(--radius-card)] text-left focus-visible:outline-none"
        aria-label={`Ver ${card.name}`}
      >
        <CardArt card={card} />
        <div className="px-0.5 pt-2">
          <p className="line-clamp-1 text-xs font-semibold text-[var(--color-ink)]">{card.name}</p>
          <p className="font-display mt-0.5 text-[9px] uppercase text-[var(--color-ink-subtle)]">
            G{card.grade}
            {card.clan ? ` · ${card.clan}` : card.nation ? ` · ${nationLabel(card.nation)}` : ""}
          </p>
        </div>
      </button>
    </div>
  );
}
