import { forwardRef, useMemo } from "react";
import type { BanlistDetail } from "@/api/banlists";
import { Avatar } from "@/components/Avatar";
import { RESTRICTION_META, GROUP_KINDS, CARD_RESTRICTIONS } from "@/lib/banlistMeta";
import { formatLabel } from "@/lib/formats";
import { GRADE_COLORS } from "@/lib/cardMeta";

const TONE_COLOR: Record<string, string> = {
  danger: "var(--color-danger)",
  warning: "var(--color-warning)",
  official: "var(--color-violet)",
  neutral: "var(--color-ink-subtle)",
};

/** Print-worthy, exportable view of a banlist. Pure text/badges — no card art —
 *  so the PNG capture never hits a cross-origin canvas taint. */
export const BanlistShowcase = forwardRef<HTMLDivElement, { banlist: BanlistDetail }>(
  function BanlistShowcase({ banlist }, ref) {
    const entries = banlist.current_version?.entries ?? [];
    const cardEntries = useMemo(() => entries.filter((e) => e.card), [entries]);
    const groupEntries = useMemo(() => entries.filter((e) => e.group), [entries]);
    const accent = "var(--color-violet)";

    // Card restrictions bucketed by type, in a sensible order.
    const buckets = CARD_RESTRICTIONS.map((type) => ({
      type,
      meta: RESTRICTION_META[type],
      items: cardEntries.filter((e) => e.restriction_type === type),
    })).filter((b) => b.items.length > 0);

    return (
      <div
        ref={ref}
        className="relative overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)]"
        style={{ boxShadow: `0 0 0 1px ${accent}22, var(--shadow-hard)` }}
      >
        {/* Hero */}
        <div className="relative overflow-hidden border-b-2 border-[var(--color-border)] p-6">
          <div
            className="pointer-events-none absolute inset-0"
            style={{ background: `linear-gradient(180deg, ${accent}22 0%, var(--color-surface) 92%)` }}
            aria-hidden
          />
          <div className="relative flex flex-wrap items-start justify-between gap-4">
            <div className="min-w-0">
              <div className="mb-2 flex flex-wrap items-center gap-2">
                <span className="font-display rounded-[4px] px-2 py-1 text-[11px] font-bold uppercase text-white" style={{ background: accent }}>
                  {banlist.is_official ? "Oficial" : "Comunidade"}
                </span>
                <span className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-[11px]">
                  {formatLabel(banlist.format_code)}
                </span>
                <span className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-[11px]">
                  v{banlist.current_version?.version}
                </span>
              </div>
              <h1 className="font-display text-2xl leading-tight sm:text-3xl">{banlist.name}</h1>
              {banlist.objective && <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{banlist.objective}</p>}
              {banlist.owner && (
                <div className="mt-3 flex items-center gap-2">
                  <Avatar avatarKey={undefined} username={banlist.owner.username} size={24} />
                  <span className="text-sm text-[var(--color-ink-muted)]">por <b className="text-[var(--color-ink)]">{banlist.owner.username}</b></span>
                </div>
              )}
            </div>
            <div className="text-right">
              <div className="font-display text-lg tracking-tight" style={{ color: accent }}>RIDE<span className="text-[var(--color-ink)]">DECK</span></div>
              <div className="mt-1 text-xs text-[var(--color-ink-subtle)]">{banlist.entry_count} regras · ♥ {banlist.like_count}</div>
            </div>
          </div>
        </div>

        <div className="space-y-5 p-6">
          {buckets.length === 0 && groupEntries.length === 0 && (
            <p className="text-sm text-[var(--color-ink-subtle)]">Esta banlist ainda não tem restrições.</p>
          )}

          {buckets.map(({ type, meta, items }) => (
            <div key={type}>
              <div className="mb-2 flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: TONE_COLOR[meta.tone] }} />
                <h2 className="font-display text-sm uppercase tracking-wide">{meta.label} ({items.length})</h2>
              </div>
              <p className="mb-2 text-xs text-[var(--color-ink-subtle)]">{meta.desc}</p>
              <div className="grid grid-cols-1 gap-1.5 sm:grid-cols-2">
                {items.map((e) => (
                  <div key={e.uuid} className="flex items-center gap-2 rounded-[6px] bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                    <span
                      className="font-display grid h-5 min-w-5 place-items-center rounded-[4px] px-1 text-[10px] font-bold text-black"
                      style={{ background: GRADE_COLORS[e.card!.grade] ?? "#888" }}
                    >
                      {e.card!.grade}
                    </span>
                    <span className="min-w-0 truncate">{e.card!.name}</span>
                  </div>
                ))}
              </div>
            </div>
          ))}

          {groupEntries.length > 0 && (
            <div>
              <div className="mb-2 flex items-center gap-2">
                <span className="h-3 w-3 rounded-full" style={{ background: accent }} />
                <h2 className="font-display text-sm uppercase tracking-wide">Grupos de escolha ({groupEntries.length})</h2>
              </div>
              <div className="space-y-2">
                {groupEntries.map((e) => {
                  const k = GROUP_KINDS[e.group!.kind];
                  return (
                    <div key={e.uuid} className="rounded-[6px] border-2 border-[var(--color-violet)]/40 bg-[var(--color-violet)]/5 p-3">
                      <div className="mb-1 flex flex-wrap items-center gap-2">
                        <span className="font-display rounded-[4px] px-2 py-0.5 text-[10px] font-bold uppercase text-white" style={{ background: accent }}>
                          {k?.label ?? e.group!.kind}
                        </span>
                        <span className="font-display text-xs uppercase">{e.group!.name}</span>
                      </div>
                      <p className="mb-2 text-[11px] text-[var(--color-ink-muted)]">{k?.desc(e.group!.limit_value)}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {e.group!.members.map((m) => (
                          <span key={m.uuid} className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-xs">
                            {m.card.name}
                          </span>
                        ))}
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        <div className="flex items-center justify-between border-t-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-6 py-3 text-xs text-[var(--color-ink-subtle)]">
          <span className="font-display" style={{ color: accent }}>RIDEDECK</span>
          <span>vanguard.kizzcross.com.br/b/{banlist.uuid.slice(0, 8)}</span>
        </div>
      </div>
    );
  },
);
