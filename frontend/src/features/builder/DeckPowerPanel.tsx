import { useQuery } from "@tanstack/react-query";
import { Gauge } from "lucide-react";
import { powerApi } from "@/api/powerlevel";

function levelColor(v: number): string {
  if (v >= 9) return "var(--color-danger)";
  if (v >= 7) return "var(--color-warning)";
  if (v >= 5) return "var(--color-accent)";
  return "var(--color-success)";
}

export function DeckPowerPanel({ deckUuid, depKey }: { deckUuid: string; depKey: string }) {
  const { data } = useQuery({
    queryKey: ["deck-power", deckUuid, depKey],
    queryFn: () => powerApi.deckPower(deckUuid),
  });
  if (!data) return null;

  return (
    <div>
      <h3 className="font-display mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
        <Gauge className="h-4 w-4 text-[var(--color-violet)]" /> Power (editorial)
      </h3>
      {!data.has_data ? (
        <p className="text-[11px] text-[var(--color-ink-subtle)]">
          Nenhuma carta avaliada neste formato ainda{data.unrated_cards ? ` (${data.unrated_cards} sem nível)` : ""}.
        </p>
      ) : (
        <>
          <div className="grid grid-cols-3 gap-2">
            {[
              ["Máx", data.max_power_level],
              ["Média pond.", data.weighted_average],
              ["Soma", data.weighted_sum],
            ].map(([label, val]) => (
              <div key={label as string} className="rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1.5 text-center">
                <div className="font-display text-[9px] uppercase text-[var(--color-ink-subtle)]">{label}</div>
                <div className="font-display text-base">{val}</div>
              </div>
            ))}
          </div>
          {data.top_contributors && data.top_contributors.length > 0 && (
            <ul className="mt-2 space-y-1">
              {data.top_contributors.map((c) => (
                <li key={c.card_uuid} className="flex items-center gap-2 text-[11px]">
                  <span className="font-display grid h-5 w-5 place-items-center rounded-[3px] text-[10px] text-[#140f00]" style={{ background: levelColor(c.value) }}>
                    {c.value}
                  </span>
                  <span className="min-w-0 flex-1 truncate">{c.name}</span>
                  <span className="text-[var(--color-ink-subtle)]">×{c.quantity}</span>
                </li>
              ))}
            </ul>
          )}
          {data.unrated_cards ? (
            <p className="mt-1.5 text-[10px] text-[var(--color-ink-subtle)]">{data.unrated_cards} cartas sem avaliação.</p>
          ) : null}
        </>
      )}
      <p className="mt-2 text-[10px] text-[var(--color-ink-subtle)]">
        Estimativa. O único dado oficial é o power level individual das cartas (definido por admins).
      </p>
    </div>
  );
}
