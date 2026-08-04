import { useState } from "react";
import type { CardListItem } from "@/api/cards";
import { GRADE_COLORS, NATION_COLORS, cardTypeLabel, nationLabel } from "@/lib/cardMeta";
import { NationCoin, NationLogo } from "@/components/NationLogo";
import { cn } from "@/lib/cn";

function GradeChip({ grade }: { grade: number }) {
  const gradeColor = GRADE_COLORS[grade] ?? "var(--color-grade-0)";
  return (
    <span
      className="font-display grid h-5 w-5 place-items-center rounded-[4px] border border-[var(--color-border)] text-[10px] text-[#140f00] shadow-[var(--shadow-hard-sm)]"
      style={{ background: gradeColor }}
    >
      {grade}
    </span>
  );
}

/** Card artwork with lazy-load + a themed placeholder face fallback. */
export function CardArt({ card, className }: { card: CardListItem; className?: string }) {
  const [loaded, setLoaded] = useState(false);
  const [failed, setFailed] = useState(false);
  const url = card.default_printing?.image_url;
  const gradeColor = GRADE_COLORS[card.grade] ?? "var(--color-grade-0)";
  const nationColor = NATION_COLORS[card.nation] ?? "var(--color-border-strong)";

  if (url && !failed) {
    return (
      <div
        className={cn(
          "relative aspect-[63/88] overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-border)]",
          "ring-1 ring-white/5 shadow-[var(--shadow-card)]",
          className,
        )}
      >
        {!loaded && <div className="rd-skeleton absolute inset-0" />}
        <img
          src={url}
          alt={card.name}
          loading="lazy"
          onLoad={() => setLoaded(true)}
          onError={() => setFailed(true)}
          className={cn("h-full w-full object-cover transition-opacity duration-300", loaded ? "opacity-100" : "opacity-0")}
        />
        {/* top gradient for chip legibility */}
        <div className="pointer-events-none absolute inset-x-0 top-0 h-10 bg-gradient-to-b from-black/45 to-transparent" />
        <span className="absolute left-1.5 top-1.5">
          <GradeChip grade={card.grade} />
        </span>
        {card.nation && (
          <span className="absolute right-1.5 top-1.5 drop-shadow">
            <NationCoin nation={card.nation} size={20} />
          </span>
        )}
      </div>
    );
  }

  // Placeholder "card face"
  return (
    <div
      className={cn(
        "relative flex aspect-[63/88] flex-col overflow-hidden rounded-[var(--radius-card)] border-2 p-2 text-white",
        "shadow-[var(--shadow-card)]",
        className,
      )}
      style={{
        background: `radial-gradient(120% 80% at 50% 0%, ${gradeColor}33, transparent 55%), linear-gradient(180deg, var(--color-surface-2), var(--color-surface))`,
        borderColor: "var(--color-border)",
      }}
    >
      <div className="flex items-center justify-between">
        <GradeChip grade={card.grade} />
        {card.trigger && (
          <span className="font-display rounded-[3px] bg-black/40 px-1.5 py-0.5 text-[8px] uppercase ring-1 ring-white/10">
            {card.trigger}
          </span>
        )}
      </div>
      <div
        className="my-2 grid flex-1 place-items-center rounded-[4px]"
        style={{ background: `${nationColor}12` }}
      >
        {card.nation ? (
          <NationLogo nation={card.nation} size={40} className="opacity-90" />
        ) : (
          <span className="font-display text-2xl text-white/15">{card.grade}</span>
        )}
      </div>
      <div>
        <p className="line-clamp-2 text-[11px] font-semibold leading-tight text-[var(--color-ink)]">
          {card.name}
        </p>
        <p className="font-display mt-0.5 flex items-center justify-between text-[8px] uppercase text-[var(--color-ink-subtle)]">
          <span>{cardTypeLabel(card.card_type)}</span>
          {card.power != null && <span className="text-[var(--color-ink-muted)]">{card.power.toLocaleString()}</span>}
        </p>
        {card.nation && (
          <p className="font-display text-[8px] uppercase" style={{ color: nationColor }}>
            {nationLabel(card.nation)}
          </p>
        )}
      </div>
    </div>
  );
}
