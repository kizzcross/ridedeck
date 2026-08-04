import { forwardRef, useMemo } from "react";
import type { DeckDetail, DeckEntry } from "@/api/decks";
import { Avatar } from "@/components/Avatar";
import { NationLogo } from "@/components/NationLogo";
import { proxiedImage } from "@/lib/cardImage";
import {
  GRADE_COLORS,
  NATION_COLORS,
  TRIGGER_COLORS,
  TRIGGER_LABELS,
  nationLabel,
} from "@/lib/cardMeta";
import { cn } from "@/lib/cn";

const FORMAT_LABEL: Record<string, string> = {
  standard: "Standard", v_premium: "V Premium", premium: "Premium", g: "G Era",
};

function ShowcaseCard({ entry, size = "md" }: { entry: DeckEntry; size?: "md" | "lg" }) {
  const img = proxiedImage(entry.card.default_printing?.image_url);
  const grade = entry.card.grade;
  return (
    <div className={cn("relative", size === "lg" ? "w-full" : "w-full")}>
      <div className="relative aspect-[63/88] overflow-hidden rounded-[8px] border-2 border-[var(--color-border)] shadow-[var(--shadow-card)]">
        {img ? (
          <img src={img} alt={entry.card.name} crossOrigin="anonymous" className="h-full w-full object-cover" />
        ) : (
          <div className="grid h-full w-full place-items-center bg-[var(--color-surface-3)] p-1 text-center text-[9px] text-[var(--color-ink-muted)]">
            {entry.card.name}
          </div>
        )}
        <span
          className="font-display absolute left-1 top-1 grid h-5 min-w-5 place-items-center rounded-[4px] border border-black/40 px-1 text-[10px] font-bold text-black"
          style={{ background: GRADE_COLORS[grade] ?? "#888" }}
        >
          {grade}
        </span>
        {entry.quantity > 1 && (
          <span className="font-display absolute bottom-1 right-1 grid h-5 min-w-5 place-items-center rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-1 text-[11px]">
            ×{entry.quantity}
          </span>
        )}
      </div>
    </div>
  );
}

function StatBar({ label, value, max, color }: { label: string; value: number; max: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="font-display w-8 text-right text-[11px] text-[var(--color-ink-muted)]">{label}</span>
      <div className="h-3 flex-1 overflow-hidden rounded-full bg-[var(--color-surface-3)]">
        <div className="h-full rounded-full" style={{ width: `${max ? (value / max) * 100 : 0}%`, background: color }} />
      </div>
      <span className="font-display w-6 text-[11px]">{value}</span>
    </div>
  );
}

/**
 * The deck "business card": a self-contained, print-worthy showcase of a deck.
 * Rendered on the public share page and captured to a PNG for export. Uses
 * proxied (same-origin) card art so the capture isn't canvas-tainted.
 */
export const DeckShowcase = forwardRef<HTMLDivElement, { deck: DeckDetail }>(function DeckShowcase(
  { deck },
  ref,
) {
  const entries = deck.current_version?.entries ?? [];
  const sortCards = (a: DeckEntry, b: DeckEntry) =>
    a.card.grade - b.card.grade || a.card.name.localeCompare(b.card.name);

  const ride = useMemo(() => entries.filter((e) => e.zone === "ride_deck").sort(sortCards), [entries]);
  const main = useMemo(() => entries.filter((e) => e.zone === "main_deck").sort(sortCards), [entries]);
  const gDeck = useMemo(() => entries.filter((e) => e.zone === "g_deck").sort(sortCards), [entries]);

  // Grade curve over the main deck (grades 0–3).
  const gradeCounts = [0, 1, 2, 3].map((g) =>
    main.filter((e) => e.card.grade === g).reduce((s, e) => s + e.quantity, 0),
  );
  const maxGrade = Math.max(1, ...gradeCounts);
  const mainTotal = main.reduce((s, e) => s + e.quantity, 0);

  // Trigger lineup.
  const triggers = new Map<string, number>();
  for (const e of main) {
    if (e.card.trigger) triggers.set(e.card.trigger, (triggers.get(e.card.trigger) ?? 0) + e.quantity);
  }
  const triggerList = [...triggers.entries()].sort((a, b) => b[1] - a[1]);

  const nation = deck.nation_focus || ride.find((e) => e.card.nation)?.card.nation || main.find((e) => e.card.nation)?.card.nation || "";
  const accent = NATION_COLORS[nation] ?? "var(--color-accent)";
  const heroArt = proxiedImage(
    ([...ride].reverse().find((e) => e.card.default_printing?.image_url) ?? main[0])?.card.default_printing?.image_url,
  );

  return (
    <div
      ref={ref}
      className="relative overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)]"
      style={{ boxShadow: `0 0 0 1px ${accent}22, var(--shadow-hard)` }}
    >
      {/* Hero */}
      <div className="relative overflow-hidden border-b-2 border-[var(--color-border)] p-6">
        {heroArt && (
          <div className="pointer-events-none absolute inset-0 opacity-30" aria-hidden>
            <img src={heroArt} crossOrigin="anonymous" alt="" className="h-full w-full scale-110 object-cover blur-2xl" />
          </div>
        )}
        <div
          className="pointer-events-none absolute inset-0"
          style={{ background: `linear-gradient(180deg, ${accent}18 0%, var(--color-surface) 92%)` }}
          aria-hidden
        />
        <div className="relative flex flex-wrap items-start justify-between gap-4">
          <div className="min-w-0">
            <div className="mb-2 flex flex-wrap items-center gap-2">
              <span className="font-display rounded-[4px] px-2 py-1 text-[11px] font-bold uppercase text-black" style={{ background: accent }}>
                {FORMAT_LABEL[deck.format_code] ?? deck.format_code}
              </span>
              {nation && (
                <span className="flex items-center gap-1.5 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-[11px]">
                  <NationLogo nation={nation} size={14} /> {nationLabel(nation)}
                </span>
              )}
              {deck.check_banlist_name && (
                <span className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-[11px]">
                  ⚖ {deck.check_banlist_name}
                </span>
              )}
            </div>
            <h1 className="font-display text-2xl leading-tight sm:text-3xl">{deck.title}</h1>
            {deck.archetype && <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{deck.archetype}</p>}
            <div className="mt-3 flex items-center gap-2">
              <Avatar avatarKey={deck.owner.avatar_key} username={deck.owner.username} size={28} />
              <span className="text-sm text-[var(--color-ink-muted)]">por <b className="text-[var(--color-ink)]">{deck.owner.username}</b></span>
            </div>
          </div>
          <div className="text-right">
            <div className="font-display text-lg tracking-tight" style={{ color: accent }}>RIDE<span className="text-[var(--color-ink)]">DECK</span></div>
            <div className="mt-1 flex justify-end gap-3 text-xs text-[var(--color-ink-subtle)]">
              <span>♥ {deck.like_count}</span>
              <span>★ {deck.favorite_count}</span>
            </div>
          </div>
        </div>
      </div>

      <div className="space-y-6 p-6">
        {/* Ride deck line */}
        {ride.length > 0 && (
          <div>
            <h2 className="font-display mb-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
              Ride Deck
            </h2>
            <div className="grid grid-cols-5 gap-2 sm:gap-3">
              {ride.map((e) => (
                <ShowcaseCard key={e.uuid} entry={e} size="lg" />
              ))}
            </div>
          </div>
        )}

        {/* Stats: grade curve + trigger lineup */}
        <div className="grid gap-4 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] p-4 sm:grid-cols-2">
          <div>
            <h3 className="font-display mb-2 text-[11px] uppercase text-[var(--color-ink-muted)]">Curva de grade · {mainTotal} cartas</h3>
            <div className="space-y-1.5">
              {gradeCounts.map((c, g) => (
                <StatBar key={g} label={`G${g}`} value={c} max={maxGrade} color={GRADE_COLORS[g]} />
              ))}
            </div>
          </div>
          <div>
            <h3 className="font-display mb-2 text-[11px] uppercase text-[var(--color-ink-muted)]">Triggers</h3>
            {triggerList.length === 0 ? (
              <p className="text-xs text-[var(--color-ink-subtle)]">—</p>
            ) : (
              <div className="flex flex-wrap gap-1.5">
                {triggerList.map(([t, n]) => (
                  <span
                    key={t}
                    className="font-display flex items-center gap-1 rounded-[4px] border-2 border-[var(--color-border)] px-2 py-1 text-[11px]"
                    style={{ background: `${TRIGGER_COLORS[t] ?? "var(--color-surface-3)"}22` }}
                  >
                    <span className="inline-block h-2.5 w-2.5 rounded-full" style={{ background: TRIGGER_COLORS[t] }} />
                    {n}× {TRIGGER_LABELS[t] ?? t}
                  </span>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Main deck grid */}
        {main.length > 0 && (
          <div>
            <h2 className="font-display mb-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
              Main Deck ({mainTotal})
            </h2>
            <div className="grid grid-cols-5 gap-2 sm:grid-cols-8 sm:gap-3">
              {main.map((e) => (
                <ShowcaseCard key={e.uuid} entry={e} />
              ))}
            </div>
          </div>
        )}

        {/* G deck */}
        {gDeck.length > 0 && (
          <div>
            <h2 className="font-display mb-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
              G Deck ({gDeck.reduce((s, e) => s + e.quantity, 0)})
            </h2>
            <div className="grid grid-cols-4 gap-2 sm:grid-cols-8 sm:gap-3">
              {gDeck.map((e) => (
                <ShowcaseCard key={e.uuid} entry={e} />
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer watermark */}
      <div className="flex items-center justify-between border-t-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-6 py-3 text-xs text-[var(--color-ink-subtle)]">
        <span className="font-display" style={{ color: accent }}>RIDEDECK</span>
        <span>vanguard.kizzcross.com.br/d/{deck.uuid.slice(0, 8)}</span>
      </div>
    </div>
  );
});
