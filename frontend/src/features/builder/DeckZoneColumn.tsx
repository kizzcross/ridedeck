import { useDroppable } from "@dnd-kit/core";
import { ImageIcon, Minus, Plus, X } from "lucide-react";
import type { DeckEntry, Zone } from "@/api/decks";
import type { CardListItem } from "@/api/cards";
import { GRADE_COLORS } from "@/lib/cardMeta";
import { NationLogo } from "@/components/NationLogo";
import { cn } from "@/lib/cn";

function EntryRow({
  entry,
  owned,
  isCover,
  onInc,
  onDec,
  onRemove,
  onSetCover,
}: {
  entry: DeckEntry;
  owned?: number;
  isCover?: boolean;
  onInc: () => void;
  onDec: () => void;
  onRemove: () => void;
  onSetCover?: () => void;
}) {
  const c = entry.card;
  const gradeColor = GRADE_COLORS[c.grade] ?? "var(--color-grade-0)";
  const missing = owned === undefined ? 0 : Math.max(0, entry.quantity - owned);
  return (
    <div className="group flex items-center gap-2 rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] p-1.5">
      <span
        className="font-display grid h-6 w-6 shrink-0 place-items-center rounded-[4px] text-[10px] text-[#140f00]"
        style={{ background: gradeColor }}
      >
        {c.grade}
      </span>
      {c.default_printing?.image_url ? (
        <img src={c.default_printing.image_url} alt="" className="h-8 w-6 shrink-0 rounded-[3px] object-cover" loading="lazy" />
      ) : c.nation ? (
        <NationLogo nation={c.nation} size={18} />
      ) : null}
      <span className="min-w-0 flex-1 truncate text-xs font-medium">
        {c.name}
        {owned !== undefined && missing > 0 && (
          <span className="font-display ml-1.5 whitespace-nowrap text-[9px] text-[var(--color-warning)]" title={`Você possui ${owned}, faltam ${missing}`}>
            ⚠ faltam {missing}
          </span>
        )}
      </span>
      <div className="flex items-center gap-1">
        {onSetCover && (
          <button
            onClick={onSetCover}
            aria-label={isCover ? "Carta principal (capa)" : "Usar como carta principal (capa)"}
            title={isCover ? "É a carta principal (capa do deck)" : "Usar como carta principal"}
            className={cn(
              "grid h-6 w-6 place-items-center rounded-[4px] border transition-colors",
              isCover
                ? "border-[var(--color-accent)] text-[var(--color-accent)]"
                : "border-transparent text-[var(--color-ink-subtle)] opacity-0 hover:text-[var(--color-accent)] group-hover:opacity-100",
            )}
          >
            <ImageIcon className={cn("h-3.5 w-3.5", isCover && "fill-current")} />
          </button>
        )}
        <button onClick={onDec} aria-label="Menos" className="grid h-6 w-6 place-items-center rounded-[4px] border border-[var(--color-border)] bg-[var(--color-surface-3)] hover:bg-[var(--color-border-strong)]">
          <Minus className="h-3 w-3" />
        </button>
        <span className="font-display w-5 text-center text-sm">{entry.quantity}</span>
        <button onClick={onInc} aria-label="Mais" className="grid h-6 w-6 place-items-center rounded-[4px] border border-[var(--color-border)] bg-[var(--color-surface-3)] hover:bg-[var(--color-border-strong)]">
          <Plus className="h-3 w-3" />
        </button>
        <button onClick={onRemove} aria-label="Remover" className="grid h-6 w-6 place-items-center rounded-[4px] text-[var(--color-ink-subtle)] opacity-0 hover:text-[var(--color-danger)] group-hover:opacity-100">
          <X className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

export function DeckZoneColumn({
  zone,
  label,
  entries,
  count,
  target,
  ownedOf,
  coverPrintingUuid,
  onInc,
  onDec,
  onRemove,
  onSetCover,
}: {
  zone: Zone;
  label: string;
  entries: DeckEntry[];
  count: number;
  target?: string;
  ownedOf?: (cardUuid: string) => number;
  coverPrintingUuid?: string | null;
  onInc: (c: CardListItem, z: Zone) => void;
  onDec: (c: CardListItem, z: Zone) => void;
  onRemove: (c: CardListItem, z: Zone) => void;
  onSetCover?: (c: CardListItem) => void;
}) {
  const { setNodeRef, isOver } = useDroppable({ id: `zone-${zone}`, data: { zone } });
  const sorted = [...entries].sort((a, b) => a.card.grade - b.card.grade || a.card.name.localeCompare(b.card.name));

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "flex min-h-[120px] flex-col rounded-[var(--radius-card)] border-2 p-2 transition-colors",
        isOver ? "border-[var(--color-accent)] bg-[var(--color-accent)]/5" : "border-[var(--color-border)] bg-[var(--color-surface)]",
      )}
    >
      <div className="mb-2 flex items-center justify-between">
        <h3 className="font-display text-xs uppercase tracking-wide">{label}</h3>
        <span className="font-display text-xs text-[var(--color-ink-muted)]">
          {count}
          {target ? <span className="text-[var(--color-ink-subtle)]">/{target}</span> : ""}
        </span>
      </div>
      {sorted.length === 0 ? (
        <div className="grid flex-1 place-items-center rounded-[6px] border-2 border-dashed border-[var(--color-border)] py-6 text-center text-[11px] text-[var(--color-ink-subtle)]">
          Arraste cartas aqui
        </div>
      ) : (
        <div className="space-y-1.5">
          {sorted.map((e) => (
            <EntryRow
              key={`${e.card.uuid}-${e.zone}`}
              entry={e}
              owned={ownedOf ? ownedOf(e.card.uuid) : undefined}
              isCover={!!coverPrintingUuid && e.card.default_printing?.uuid === coverPrintingUuid}
              onInc={() => onInc(e.card, zone)}
              onDec={() => onDec(e.card, zone)}
              onRemove={() => onRemove(e.card, zone)}
              onSetCover={onSetCover ? () => onSetCover(e.card) : undefined}
            />
          ))}
        </div>
      )}
    </div>
  );
}
