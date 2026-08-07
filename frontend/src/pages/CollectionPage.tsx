import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Library, Search } from "lucide-react";
import { collectionApi, type CollectionItem } from "@/api/collection";
import { useDebounce } from "@/hooks/useDebounce";
import { useOwnedMap } from "@/hooks/useOwnedMap";
import { CardArt } from "@/features/catalog/CardArt";
import { CardDetailDrawer } from "@/features/catalog/CardDetailDrawer";
import { Badge, Panel, Skeleton } from "@/components/ui";
import { cn } from "@/lib/cn";

function OwnedTile({ item, onOpen }: { item: CollectionItem; onOpen: (slug: string) => void }) {
  return (
    <button onClick={() => onOpen(item.card.slug)} className="rd-card group relative flex flex-col rounded-[var(--radius-card)] text-left">
      <CardArt card={item.card} />
      <span className="font-display absolute right-1 top-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-accent)] px-1.5 py-0.5 text-[10px] text-[#1a1400]">
        ×{item.owned_quantity}
      </span>
      <p className="mt-1.5 line-clamp-1 px-0.5 text-xs font-semibold">{item.card.name}</p>
    </button>
  );
}

export function CollectionPage() {
  const [raw, setRaw] = useState("");
  const search = useDebounce(raw, 300);
  const [era, setEra] = useState("");
  const [openSlug, setOpenSlug] = useState<string | null>(null);
  useOwnedMap(); // keep owned map warm for the drawer control

  const { data, isLoading } = useQuery({
    queryKey: ["collection", search, era],
    queryFn: () => collectionApi.list(search, era),
  });
  const { data: summary } = useQuery({ queryKey: ["collection-summary"], queryFn: collectionApi.summary });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl"><span className="text-gradient">Minha Coleção</span></h1>
          <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
            {summary?.distinct_cards ?? 0} cartas distintas · {summary?.total_cards ?? 0} no total
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative min-w-[220px] flex-1 sm:max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-ink-subtle)]" />
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Buscar na coleção…"
            className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] pl-9 pr-3 text-sm focus:border-[var(--color-accent)]"
          />
        </div>
        <div className="flex gap-1">
          {[
            ["", "Todas"],
            ["g", "G era"],
            ["d", "D era"],
            ["v", "V era"],
          ].map(([value, label]) => (
            <button
              key={value}
              onClick={() => setEra(value)}
              className={cn(
                "font-display h-10 rounded-[var(--radius-card)] border-2 px-3 text-[11px] uppercase",
                era === value
                  ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
              )}
            >
              {label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">
          {Array.from({ length: 8 }).map((_, i) => <Skeleton key={i} className="aspect-[63/88]" />)}
        </div>
      ) : (data?.results.length ?? 0) === 0 ? (
        <Panel className="p-10 text-center">
          <Library className="mx-auto mb-3 h-10 w-10 text-[var(--color-ink-subtle)]" />
          <p className="font-display">Coleção vazia</p>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Abra uma carta no catálogo e use o controle <Badge tone="accent">Na coleção</Badge> para adicioná-la.
          </p>
        </Panel>
      ) : (
        <div className="grid grid-cols-3 gap-3 sm:grid-cols-4 md:grid-cols-6 xl:grid-cols-8">
          {data!.results.map((item) => (
            <OwnedTile key={item.uuid} item={item} onOpen={setOpenSlug} />
          ))}
        </div>
      )}

      <CardDetailDrawer slug={openSlug} onClose={() => setOpenSlug(null)} />
    </div>
  );
}
