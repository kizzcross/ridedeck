import { useMemo, useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { Search, SlidersHorizontal, X } from "lucide-react";
import { cardsApi, type CardListItem } from "@/api/cards";
import { useDebounce } from "@/hooks/useDebounce";
import { Badge, Button, Skeleton } from "@/components/ui";
import { CardTile } from "@/features/catalog/CardTile";
import { CardDetailDrawer } from "@/features/catalog/CardDetailDrawer";
import { CatalogFilters, EMPTY_FILTERS, type Filters } from "@/features/catalog/CatalogFilters";

const PAGE_SIZE = 24;

export function CatalogPage() {
  const [rawSearch, setRawSearch] = useState("");
  const search = useDebounce(rawSearch, 300);
  const [filters, setFilters] = useState<Filters>(EMPTY_FILTERS);
  const [openSlug, setOpenSlug] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data: sets } = useQuery({ queryKey: ["sets"], queryFn: cardsApi.sets });
  const setOptions = useMemo<[string, string][]>(
    () => (sets ?? []).map((s) => [s.code, s.name]),
    [sets],
  );

  const query = useInfiniteQuery({
    queryKey: ["cards", search, filters],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      cardsApi.list({ search, ...filters, page: pageParam, page_size: PAGE_SIZE }),
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
  });

  const cards: CardListItem[] = query.data?.pages.flatMap((p) => p.results) ?? [];
  const total = query.data?.pages[0]?.count ?? 0;
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="flex gap-6">
      {/* Filters — desktop sidebar */}
      <aside className="hidden w-56 shrink-0 lg:block">
        <div className="sticky top-20 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
          <CatalogFilters filters={filters} onChange={setFilters} sets={setOptions} />
        </div>
      </aside>

      <div className="min-w-0 flex-1">
        <div className="mb-4 flex items-end justify-between gap-3">
          <div>
            <h1 className="font-display text-2xl">
              <span className="text-gradient">Catálogo</span>
            </h1>
            <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
              {total.toLocaleString()} {total === 1 ? "carta" : "cartas"}
            </p>
          </div>
        </div>

        {/* Search bar */}
        <div className="mb-4 flex gap-2">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-ink-subtle)]" />
            <input
              value={rawSearch}
              onChange={(e) => setRawSearch(e.target.value)}
              placeholder="Buscar por nome ou texto de habilidade…"
              aria-label="Buscar cartas"
              className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] pl-9 pr-9 text-sm focus:border-[var(--color-accent)]"
            />
            {rawSearch && (
              <button
                onClick={() => setRawSearch("")}
                aria-label="Limpar busca"
                className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)]"
              >
                <X className="h-4 w-4" />
              </button>
            )}
          </div>
          <Button
            variant="outline"
            className="lg:hidden"
            onClick={() => setShowFilters((s) => !s)}
          >
            <SlidersHorizontal className="h-4 w-4" />
            {activeFilterCount > 0 && <Badge tone="accent">{activeFilterCount}</Badge>}
          </Button>
        </div>

        {/* Filters — mobile collapsible */}
        {showFilters && (
          <div className="mb-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4 lg:hidden">
            <CatalogFilters filters={filters} onChange={setFilters} sets={setOptions} />
          </div>
        )}

        {/* Grid */}
        {query.isLoading ? (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
            {Array.from({ length: 12 }).map((_, i) => (
              <Skeleton key={i} className="aspect-[63/88]" />
            ))}
          </div>
        ) : cards.length === 0 ? (
          <div className="rounded-xl border border-dashed border-[var(--color-border)] py-16 text-center">
            <p className="font-display text-lg">Nenhuma carta encontrada</p>
            <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
              Ajuste a busca ou os filtros.
            </p>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4 xl:grid-cols-6">
              {cards.map((card) => (
                <CardTile key={card.uuid} card={card} onOpen={(c) => setOpenSlug(c.slug)} />
              ))}
            </div>
            {query.hasNextPage && (
              <div className="mt-6 flex justify-center">
                <Button
                  variant="secondary"
                  loading={query.isFetchingNextPage}
                  onClick={() => query.fetchNextPage()}
                >
                  Carregar mais
                </Button>
              </div>
            )}
          </>
        )}
      </div>

      <CardDetailDrawer slug={openSlug} onClose={() => setOpenSlug(null)} />
    </div>
  );
}
