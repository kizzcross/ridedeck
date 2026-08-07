import { useMemo, useState } from "react";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useDraggable } from "@dnd-kit/core";
import { Plus, Search } from "lucide-react";
import { cardsApi, type CardListItem } from "@/api/cards";
import { useDebounce } from "@/hooks/useDebounce";
import { CardArt } from "@/features/catalog/CardArt";
import { Button, Skeleton } from "@/components/ui";
import { defaultZoneForGrade } from "./zones";
import { cn } from "@/lib/cn";
import type { Zone } from "@/api/decks";
import type { RestrictionInfo } from "@/api/banlists";

const RESTRICTION_LABEL: Record<string, string> = {
  banned: "BANIDA",
  limit_to_1: "MÁX 1",
  limit_to_2: "MÁX 2",
  limit_to_n: "LIMITE",
  first_vanguard_forbidden: "1ª VG PROIBIDA",
  choice_restriction: "CHOICE",
  max_distinct_from_group: "GRUPO",
  max_total_from_group: "GRUPO",
};

function DraggableCard({
  card,
  restriction,
  onAdd,
}: {
  card: CardListItem;
  restriction?: RestrictionInfo;
  onAdd: (c: CardListItem, z: Zone) => void;
}) {
  const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
    id: `search-${card.uuid}`,
    data: { card },
    disabled: restriction?.type === "banned",
  });
  const banned = restriction?.type === "banned";
  return (
    <div
      ref={setNodeRef}
      {...(banned ? {} : listeners)}
      {...attributes}
      className={cn("group relative touch-none", banned ? "cursor-not-allowed" : "cursor-grab",
        isDragging ? "opacity-40" : "")}
    >
      <div className={cn(banned && "opacity-55 grayscale")}>
        <CardArt card={card} />
      </div>
      {restriction && (
        <span
          className={cn(
            "font-display absolute left-1 top-1 z-10 rounded-[3px] border-2 border-[var(--color-border)] px-1 py-0.5 text-[8px] uppercase",
            banned ? "bg-[var(--color-danger)] text-[#2a0000]" : "bg-[var(--color-warning)] text-[#1a1400]",
          )}
          title={restriction.group ? `Grupo: ${restriction.group}` : RESTRICTION_LABEL[restriction.type]}
        >
          {RESTRICTION_LABEL[restriction.type] ?? "RESTRITA"}
        </span>
      )}
      {!banned && (
        <button
          onClick={() => onAdd(card, defaultZoneForGrade(card.grade))}
          className="absolute inset-x-1 bottom-1 flex items-center justify-center gap-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-accent)] py-0.5 text-[10px] font-bold uppercase text-[#1a1400] opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
          aria-label={`Adicionar ${card.name}`}
        >
          <Plus className="h-3 w-3" /> Add
        </button>
      )}
    </div>
  );
}

const GRADE_TABS = ["", "0", "1", "2", "3", "4"];

export function CardSearchPanel({
  onAdd,
  formatCode,
  restrictions,
}: {
  onAdd: (c: CardListItem, z: Zone) => void;
  formatCode?: string;
  restrictions?: Record<string, RestrictionInfo>;
}) {
  const [raw, setRaw] = useState("");
  const search = useDebounce(raw, 300);
  const [grade, setGrade] = useState("");
  const [gOnly, setGOnly] = useState(false);
  const [formatOnly, setFormatOnly] = useState(false);

  const query = useInfiniteQuery({
    queryKey: ["builder-cards", search, grade, gOnly, formatOnly ? formatCode : ""],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      cardsApi.list({
        search,
        grade: gOnly ? undefined : grade,
        card_type: gOnly ? "g_unit" : undefined,
        format_code: formatOnly ? formatCode : undefined,
        page: pageParam,
        page_size: 30,
      }),
    getNextPageParam: (last, pages) => (last.next ? pages.length + 1 : undefined),
  });
  const cards = useMemo(() => query.data?.pages.flatMap((p) => p.results) ?? [], [query.data]);

  return (
    <div className="flex h-full flex-col">
      <div className="mb-2 space-y-2">
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-ink-subtle)]" />
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Buscar cartas…"
            className="h-9 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] pl-8 pr-2 text-sm focus:border-[var(--color-accent)]"
          />
        </div>
        <div className="flex gap-1">
          {GRADE_TABS.map((g) => (
            <button
              key={g}
              onClick={() => {
                setGrade(g);
                setGOnly(false);
              }}
              className={cn(
                "font-display h-7 flex-1 rounded-[4px] border-2 text-[10px] uppercase",
                grade === g && !gOnly
                  ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
              )}
            >
              {g === "" ? "Tudo" : `G${g}`}
            </button>
          ))}
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setGOnly((v) => !v)}
            title="Somente G Units (para o G Deck)"
            className={cn(
              "font-display h-7 flex-1 rounded-[4px] border-2 text-[10px] uppercase",
              gOnly
                ? "border-[var(--color-border)] bg-[var(--color-violet)] text-[#140a1f]"
                : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
            )}
          >
            ⚡ Só G Units
          </button>
          {formatCode && (
            <button
              onClick={() => setFormatOnly((v) => !v)}
              title={`Somente cartas legais em ${formatCode}`}
              className={cn(
                "font-display h-7 flex-1 rounded-[4px] border-2 text-[10px] uppercase",
                formatOnly
                  ? "border-[var(--color-border)] bg-[var(--color-cyan)] text-[#04222a]"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
              )}
            >
              Legal: {formatCode}
            </button>
          )}
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto pr-1">
        {query.isLoading ? (
          <div className="grid grid-cols-3 gap-2">
            {Array.from({ length: 9 }).map((_, i) => <Skeleton key={i} className="aspect-[63/88]" />)}
          </div>
        ) : cards.length === 0 ? (
          <p className="py-8 text-center text-xs text-[var(--color-ink-subtle)]">Nenhuma carta.</p>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-2">
              {cards.map((c) => (
                <DraggableCard key={c.uuid} card={c} restriction={restrictions?.[c.uuid]} onAdd={onAdd} />
              ))}
            </div>
            {query.hasNextPage && (
              <div className="mt-3 flex justify-center">
                <Button size="sm" variant="secondary" loading={query.isFetchingNextPage} onClick={() => query.fetchNextPage()}>
                  Mais
                </Button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
