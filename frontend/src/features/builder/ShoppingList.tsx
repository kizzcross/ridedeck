import { useQuery } from "@tanstack/react-query";
import { ShoppingCart } from "lucide-react";
import { collectionApi } from "@/api/collection";
import { useAuth } from "@/hooks/useAuth";

export function ShoppingList({ deckUuid, depKey }: { deckUuid: string; depKey: string }) {
  const authed = useAuth((s) => s.status === "authenticated");
  const { data } = useQuery({
    queryKey: ["deck-collection-report", deckUuid, depKey],
    queryFn: () => collectionApi.deckReport(deckUuid),
    enabled: authed,
  });

  if (!data) return null;
  const { summary, shopping_list } = data;

  return (
    <div>
      <h3 className="font-display mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
        <ShoppingCart className="h-4 w-4 text-[var(--color-accent)]" /> Coleção
      </h3>

      <div className="mb-2">
        <div className="mb-1 flex items-center justify-between text-[11px]">
          <span className="text-[var(--color-ink-muted)]">Possuído</span>
          <span className="font-display">{summary.owned_pct}%</span>
        </div>
        <div className="h-2.5 overflow-hidden rounded-[3px] border-2 border-[var(--color-border)]">
          <div className="h-full bg-[var(--color-success)]" style={{ width: `${summary.owned_pct}%` }} />
        </div>
        <p className="mt-1 text-[10px] text-[var(--color-ink-subtle)]">
          {summary.owned}/{summary.used} cartas · faltam {summary.missing}
          {summary.missing_cost_estimate ? ` · ~$${summary.missing_cost_estimate}` : ""}
        </p>
      </div>

      {shopping_list.length > 0 && (
        <ul className="max-h-40 space-y-1 overflow-y-auto pr-1">
          {shopping_list.map((l) => (
            <li key={l.card_uuid} className="flex items-center justify-between gap-2 rounded-[4px] bg-[var(--color-surface-2)] px-2 py-1 text-[11px]">
              <span className="min-w-0 flex-1 truncate">{l.card_name}</span>
              <span className="font-display text-[var(--color-warning)]">×{l.missing}</span>
              {l.line_cost && <span className="font-display text-[var(--color-ink-muted)]">${l.line_cost}</span>}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-2 text-[10px] text-[var(--color-ink-subtle)]">
        Coleção nunca invalida o deck — apenas indica o que falta.
      </p>
    </div>
  );
}
