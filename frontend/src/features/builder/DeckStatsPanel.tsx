import { AlertTriangle, CheckCircle2, XCircle } from "lucide-react";
import type { DeckEntry, ValidationResult, Zone } from "@/api/decks";
import { GRADE_COLORS } from "@/lib/cardMeta";

function Bar({ counts }: { counts: Record<number, number> }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0) || 1;
  return (
    <div className="flex h-3 overflow-hidden rounded-[3px] border-2 border-[var(--color-border)]">
      {[0, 1, 2, 3, 4].map((g) => {
        const w = ((counts[g] ?? 0) / total) * 100;
        return w > 0 ? (
          <div key={g} style={{ width: `${w}%`, background: GRADE_COLORS[g] }} title={`Grade ${g}: ${counts[g]}`} />
        ) : null;
      })}
    </div>
  );
}

export function DeckStatsPanel({
  entries,
  zoneCounts,
  validation,
}: {
  entries: DeckEntry[];
  zoneCounts: Record<Zone, number>;
  validation?: ValidationResult;
}) {
  const gradeCounts: Record<number, number> = {};
  let triggers = 0;
  entries.forEach((e) => {
    gradeCounts[e.card.grade] = (gradeCounts[e.card.grade] ?? 0) + e.quantity;
    if (e.card.trigger) triggers += e.quantity;
  });
  const total = Object.values(zoneCounts).reduce((a, b) => a + b, 0);

  return (
    <div className="space-y-4">
      <div>
        <h3 className="font-display mb-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">Curva de grade</h3>
        <Bar counts={gradeCounts} />
        <div className="mt-2 grid grid-cols-5 gap-1 text-center">
          {[0, 1, 2, 3, 4].map((g) => (
            <div key={g} className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] py-1">
              <div className="font-display text-[9px]" style={{ color: GRADE_COLORS[g] }}>G{g}</div>
              <div className="font-display text-sm">{gradeCounts[g] ?? 0}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-2">
        {[
          ["Total", total],
          ["Main", zoneCounts.main_deck],
          ["Ride", zoneCounts.ride_deck],
          ["Triggers", triggers],
        ].map(([label, val]) => (
          <div key={label as string} className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2">
            <div className="font-display text-[9px] uppercase text-[var(--color-ink-subtle)]">{label}</div>
            <div className="font-display text-lg">{val}</div>
          </div>
        ))}
      </div>

      <div>
        <h3 className="font-display mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
          Validação
          {validation && (validation.is_valid ? (
            <CheckCircle2 className="h-4 w-4 text-[var(--color-success)]" />
          ) : (
            <XCircle className="h-4 w-4 text-[var(--color-danger)]" />
          ))}
        </h3>
        {!validation ? (
          <p className="text-xs text-[var(--color-ink-subtle)]">Calculando…</p>
        ) : validation.is_valid && validation.warnings.length === 0 ? (
          <div className="flex items-center gap-2 rounded-[6px] border-2 border-[var(--color-success)]/40 bg-[var(--color-success)]/10 px-3 py-2 text-xs text-[var(--color-success)]">
            <CheckCircle2 className="h-4 w-4" /> Deck válido (regras básicas).
          </div>
        ) : (
          <ul className="space-y-1.5">
            {validation.errors.map((e, i) => (
              <li key={`e${i}`} className="flex items-start gap-2 rounded-[6px] border-2 border-[var(--color-danger)]/40 bg-[var(--color-danger)]/10 px-2.5 py-1.5 text-[11px] text-[var(--color-danger)]">
                <XCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {e.message}
              </li>
            ))}
            {validation.warnings.map((w, i) => (
              <li key={`w${i}`} className="flex items-start gap-2 rounded-[6px] border-2 border-[var(--color-warning)]/40 bg-[var(--color-warning)]/10 px-2.5 py-1.5 text-[11px] text-[var(--color-warning)]">
                <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" /> {w.message}
              </li>
            ))}
          </ul>
        )}
        <p className="mt-2 text-[10px] text-[var(--color-ink-subtle)]">
          Validação básica (Fase 3). O motor completo com banlist e power level chega na Fase 5.
        </p>
      </div>
    </div>
  );
}
