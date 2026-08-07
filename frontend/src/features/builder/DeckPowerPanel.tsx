import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Star } from "lucide-react";
import { decksApi } from "@/api/decks";
import { useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const STAR_LABELS = ["", "Casual", "Fun", "Sólido", "Forte", "Meta"];

/** Owner-chosen deck strength (1–5 pixel stars). Replaces the old editorial
 *  per-card power aggregate. Persists to Deck.power_stars. */
export function DeckPowerPanel({ deckUuid }: { deckUuid: string; depKey?: string }) {
  const qc = useQueryClient();
  const toast = useToast();
  const [hover, setHover] = useState(0);

  const { data: deck } = useQuery({
    queryKey: ["deck", deckUuid],
    queryFn: () => decksApi.detail(deckUuid),
  });

  const mut = useMutation({
    mutationFn: (value: number | null) => decksApi.update(deckUuid, { power_stars: value }),
    onSuccess: (updated) => {
      qc.setQueryData(["deck", deckUuid], updated);
      qc.invalidateQueries({ queryKey: ["my-decks"] });
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const value = deck?.power_stars ?? 0;
  const shown = hover || value;

  const pick = (n: number) => {
    // Click the current value again to clear it.
    mut.mutate(value === n ? null : n);
  };

  return (
    <div>
      <h3 className="font-display mb-2 flex items-center gap-2 text-xs uppercase tracking-wide text-[var(--color-ink-muted)]">
        <Star className="h-4 w-4 text-[var(--color-accent)]" /> Nível do deck
      </h3>

      <div className="flex items-center gap-1" onMouseLeave={() => setHover(0)}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            aria-label={`${n} estrela${n > 1 ? "s" : ""}`}
            disabled={mut.isPending}
            onMouseEnter={() => setHover(n)}
            onClick={() => pick(n)}
            className={cn(
              "grid h-8 w-8 place-items-center rounded-[4px] border-2 transition-colors",
              n <= shown
                ? "border-[var(--color-accent)] bg-[var(--color-accent)]/15"
                : "border-[var(--color-border)] bg-[var(--color-surface-2)]",
            )}
          >
            <Star
              className={cn(
                "h-4 w-4",
                n <= shown ? "fill-[var(--color-accent)] text-[var(--color-accent)]" : "text-[var(--color-ink-subtle)]",
              )}
              style={{ imageRendering: "pixelated" }}
            />
          </button>
        ))}
        <span className="font-display ml-2 text-[11px] text-[var(--color-ink-muted)]">
          {value ? `${value}★ · ${STAR_LABELS[value]}` : "sem nível"}
        </span>
      </div>

      <p className="mt-2 text-[10px] text-[var(--color-ink-subtle)]">
        Você define a força do deck de 1 a 5. Usado como orçamento nos torneios de Pool de Decks.
      </p>
    </div>
  );
}
