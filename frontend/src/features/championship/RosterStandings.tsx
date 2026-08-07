import { Crown, TrendingUp } from "lucide-react";
import type { RosterStandingRow } from "@/api/tournaments";
import { Avatar } from "@/components/Avatar";
import { Panel } from "@/components/ui";
import { cn } from "@/lib/cn";

/** Rich championship standings: points + record, Ace wins, penalties and a
 *  per-deck win-rate breakdown that expands under each player. */
export function RosterStandings({ rows, aceTiebreak }: { rows: RosterStandingRow[]; aceTiebreak?: boolean }) {
  if (!rows.length) {
    return <Panel className="p-8 text-center text-sm text-[var(--color-ink-subtle)]">A classificação aparece assim que as partidas começarem.</Panel>;
  }
  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <Panel key={r.participant.uuid} className="p-3">
          <div className="flex items-center gap-3">
            <span className={cn("font-display grid h-7 w-7 place-items-center rounded-[6px] text-sm",
              r.rank === 1 ? "bg-[var(--color-accent)] text-[#1a1400]" : "bg-[var(--color-surface-3)] text-[var(--color-ink-muted)]")}>
              {r.rank}
            </span>
            <Avatar avatarKey={r.participant.avatar_key} username={r.participant.username} size={28} />
            <span className="min-w-0 flex-1 truncate font-display">{r.participant.username}</span>
            {aceTiebreak && r.ace_wins > 0 && (
              <span className="flex items-center gap-1 text-[11px] text-[var(--color-accent)]" title="Vitórias com o Ace">
                <Crown className="h-3.5 w-3.5 fill-current" /> {r.ace_wins}
              </span>
            )}
            {r.penalties !== 0 && (
              <span className="text-[11px] text-[var(--color-danger)]" title="Penalidades">{r.penalties} pen.</span>
            )}
            <span className="font-display text-xs text-[var(--color-ink-muted)]">{r.wins}V {r.losses}D{r.draws ? ` ${r.draws}E` : ""}</span>
            <span className="font-display text-base tabular-nums text-[var(--color-ink)]">{r.points}<span className="text-[10px] text-[var(--color-ink-subtle)]"> pts</span></span>
          </div>

          {/* Per-deck win-rate */}
          {r.decks.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5 border-t border-[var(--color-border)] pt-2">
              {r.decks.map((d, i) => (
                <span key={i} className={cn("inline-flex items-center gap-1 rounded-[4px] border px-1.5 py-0.5 text-[10px]",
                  d.is_ace ? "border-[var(--color-accent)]/50 text-[var(--color-accent)]" : "border-[var(--color-border)] text-[var(--color-ink-muted)]")}
                  title={`${d.wins}V ${d.losses}D`}>
                  {d.is_ace && <Crown className="h-2.5 w-2.5 fill-current" />}
                  <span className="max-w-[9rem] truncate">{d.label}</span>
                  {d.win_rate != null && <span className="flex items-center gap-0.5 opacity-80"><TrendingUp className="h-2.5 w-2.5" />{Math.round(d.win_rate * 100)}%</span>}
                </span>
              ))}
            </div>
          )}
        </Panel>
      ))}
    </div>
  );
}
