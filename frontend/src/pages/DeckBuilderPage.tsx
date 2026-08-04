import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { Check, Cloud, Redo2, Undo2, Globe, Lock, Link2, Library, Layers, BarChart3 } from "lucide-react";
import { decksApi, type Visibility, type Zone } from "@/api/decks";
import { banlistsApi } from "@/api/banlists";
import type { CardListItem } from "@/api/cards";
import { useDeckBuilder } from "@/features/builder/useDeckBuilder";
import { useOwnedMap } from "@/hooks/useOwnedMap";
import { CardSearchPanel } from "@/features/builder/CardSearchPanel";
import { DeckZoneColumn } from "@/features/builder/DeckZoneColumn";
import { DeckStatsPanel } from "@/features/builder/DeckStatsPanel";
import { ShoppingList } from "@/features/builder/ShoppingList";
import { DeckPowerPanel } from "@/features/builder/DeckPowerPanel";
import { CardArt } from "@/features/catalog/CardArt";
import { ZONES } from "@/features/builder/zones";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { cn } from "@/lib/cn";

const FORMAT_TARGETS: Record<string, Partial<Record<Zone, string>>> = {
  standard: { main_deck: "50", ride_deck: "5" },
  v_premium: { main_deck: "50" },
  premium: { main_deck: "50" },
  g: { main_deck: "50" },
};
const FORMAT_LABEL: Record<string, string> = {
  standard: "Standard", v_premium: "V Premium", premium: "Premium", g: "G Era",
};
const SAVE_LABEL = { idle: "", saving: "Salvando…", saved: "Salvo", error: "Erro ao salvar" };
const MOBILE_TABS = [
  { key: "cards", label: "Cartas", icon: Library },
  { key: "deck", label: "Deck", icon: Layers },
  { key: "stats", label: "Stats", icon: BarChart3 },
] as const;
type MobileTab = (typeof MOBILE_TABS)[number]["key"];

export function DeckBuilderPage() {
  const { uuid = "" } = useParams();
  const toast = useToast();
  const qc = useQueryClient();
  const b = useDeckBuilder(uuid);
  const { ownedOf } = useOwnedMap();
  const [dragging, setDragging] = useState<CardListItem | null>(null);
  const [visibility, setVisibility] = useState<Visibility | null>(null);
  const [format, setFormat] = useState<string | null>(null);
  const [banlist, setBanlist] = useState<string | null | undefined>(undefined);
  const [tab, setTab] = useState<MobileTab>("cards");
  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

  useEffect(() => {
    if (b.deck) {
      setVisibility((v) => v ?? b.deck!.visibility);
      setFormat((f) => f ?? b.deck!.format_code);
      setBanlist((bl) => (bl === undefined ? b.deck!.check_banlist_uuid : bl));
    }
  }, [b.deck]);

  const vis = visibility ?? b.deck?.visibility ?? "private";
  const fmt = format ?? b.deck?.format_code ?? "standard";
  const selectedBanlist = banlist ?? null;
  const targets = FORMAT_TARGETS[fmt] ?? {};

  // Banlists selectable for this format (official + community).
  const { data: banlistsData } = useQuery({
    queryKey: ["banlists-for-format", fmt],
    queryFn: () => banlistsApi.list({ format_code: fmt }),
  });
  const banlistOptions = banlistsData?.results ?? [];

  // Restriction map for the selected banlist → mark banned/limited cards.
  const { data: restrictions } = useQuery({
    queryKey: ["banlist-restrictions", selectedBanlist],
    queryFn: () => banlistsApi.restrictionMap(selectedBanlist!),
    enabled: !!selectedBanlist,
  });

  const changeBanlist = async (uuidValue: string) => {
    const value = uuidValue || null;
    setBanlist(value);
    await decksApi.update(uuid, { check_banlist_uuid: value });
    qc.invalidateQueries({ queryKey: ["deck-validate", uuid] });
    b.refetch();
  };

  const onDragStart = (e: DragStartEvent) => setDragging((e.active.data.current?.card as CardListItem) ?? null);
  const onDragEnd = (e: DragEndEvent) => {
    setDragging(null);
    const card = e.active.data.current?.card as CardListItem | undefined;
    const zone = e.over?.data.current?.zone as Zone | undefined;
    if (card && zone) b.add(card, zone);
  };

  const publish = async (v: Visibility) => {
    await decksApi.publish(uuid, v);
    setVisibility(v);
    toast.success(v === "public" ? "Deck publicado!" : "Visibilidade atualizada");
  };

  const changeFormat = async (f: string) => {
    setFormat(f);
    await decksApi.update(uuid, { format_code: f });
    qc.invalidateQueries({ queryKey: ["deck-validate", uuid] });
    toast.info("Formato alterado", FORMAT_LABEL[f]);
  };

  if (b.isLoading || !b.deck) {
    return <div className="space-y-4"><Skeleton className="h-12 w-full" /><Skeleton className="h-[60vh] w-full" /></div>;
  }

  const VisIcon = vis === "public" ? Globe : vis === "unlisted" ? Link2 : Lock;

  const cardsPanel = <CardSearchPanel onAdd={b.add} formatCode={fmt} restrictions={restrictions} />;
  const deckPanel = (
    <div className="space-y-3">
      {ZONES.map((z) => (
        <DeckZoneColumn
          key={z.key}
          zone={z.key}
          label={z.label}
          entries={b.entries.filter((e) => e.zone === z.key)}
          count={b.zoneCounts[z.key]}
          target={targets[z.key]}
          ownedOf={ownedOf}
          onInc={b.add}
          onDec={b.decrement}
          onRemove={b.removeAll}
        />
      ))}
    </div>
  );
  const depKey = `${b.entries.length}-${b.zoneCounts.main_deck}-${b.zoneCounts.ride_deck}-${fmt}`;
  const statsPanel = (
    <>
      <DeckStatsPanel entries={b.entries} zoneCounts={b.zoneCounts} validation={b.validation} />
      <div className="mt-4 border-t-2 border-[var(--color-border)] pt-4">
        <DeckPowerPanel deckUuid={uuid} depKey={depKey} />
      </div>
      <div className="mt-4 border-t-2 border-[var(--color-border)] pt-4">
        <ShoppingList deckUuid={uuid} depKey={depKey} />
      </div>
    </>
  );

  return (
    <DndContext sensors={sensors} onDragStart={onDragStart} onDragEnd={onDragEnd}>
      {/* Top bar */}
      <div className="mb-3 flex flex-wrap items-center gap-x-3 gap-y-2">
        <div className="min-w-0 flex-1">
          <input
            defaultValue={b.deck.title}
            onBlur={(e) => e.target.value !== b.deck?.title && decksApi.update(uuid, { title: e.target.value })}
            className="font-display w-full truncate bg-transparent text-lg focus:outline-none sm:text-xl"
            aria-label="Nome do deck"
          />
          <span className="flex items-center gap-1 text-xs text-[var(--color-ink-subtle)]">
            {b.saveState === "saved" && <Check className="h-3 w-3 text-[var(--color-success)]" />}
            {b.saveState === "saving" && <Cloud className="h-3 w-3 animate-pulse" />}
            {SAVE_LABEL[b.saveState]}
          </span>
        </div>
        <div className="flex flex-wrap items-center gap-1.5">
          <Button size="sm" variant="ghost" disabled={!b.canUndo} onClick={b.undo} aria-label="Desfazer" title="Desfazer (Ctrl+Z)">
            <Undo2 className="h-4 w-4" />
          </Button>
          <Button size="sm" variant="ghost" disabled={!b.canRedo} onClick={b.redo} aria-label="Refazer" title="Refazer (Ctrl+Shift+Z)">
            <Redo2 className="h-4 w-4" />
          </Button>
          <select
            value={fmt}
            onChange={(e) => changeFormat(e.target.value)}
            className="h-8 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs"
            aria-label="Formato do deck"
          >
            <option value="standard">Standard</option>
            <option value="v_premium">V Premium</option>
            <option value="premium">Premium</option>
            <option value="g">G Era</option>
          </select>
          <select
            value={selectedBanlist ?? ""}
            onChange={(e) => changeBanlist(e.target.value)}
            className="h-8 max-w-[9rem] rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs"
            aria-label="Banlist para validar"
            title="Valide o deck contra uma banlist"
          >
            <option value="">Sem banlist</option>
            {banlistOptions.map((bl) => (
              <option key={bl.uuid} value={bl.uuid}>
                {bl.is_official ? "★ " : ""}{bl.name}
              </option>
            ))}
          </select>
          <select
            value={vis}
            onChange={(e) => publish(e.target.value as Visibility)}
            className="h-8 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs"
            aria-label="Visibilidade"
          >
            <option value="private">Privado</option>
            <option value="unlisted">Não listado</option>
            <option value="public">Público</option>
          </select>
          <Badge tone={vis === "public" ? "success" : "neutral"} className="hidden sm:inline-flex">
            <VisIcon className="h-3 w-3" /> {vis}
          </Badge>
        </div>
      </div>

      {/* Mobile tab switcher */}
      <div className="mb-3 grid grid-cols-3 gap-1 lg:hidden">
        {MOBILE_TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              "font-display flex items-center justify-center gap-1.5 rounded-[var(--radius-card)] border-2 py-2 text-[11px] uppercase",
              tab === key
                ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
            )}
          >
            <Icon className="h-4 w-4" /> {label}
            {key === "deck" && <span className="opacity-70">({b.zoneCounts.main_deck})</span>}
          </button>
        ))}
      </div>

      {/* Desktop: three columns */}
      <div className="hidden gap-4 lg:grid lg:grid-cols-[280px_1fr_270px]">
        <Panel className="h-[calc(100dvh-9rem)] p-3 lg:sticky lg:top-20">{cardsPanel}</Panel>
        <div>{deckPanel}</div>
        <Panel className="h-fit p-4 lg:sticky lg:top-20">{statsPanel}</Panel>
      </div>

      {/* Mobile: one panel at a time */}
      <div className="lg:hidden">
        {tab === "cards" && <Panel className="h-[calc(100dvh-13rem)] p-3">{cardsPanel}</Panel>}
        {tab === "deck" && deckPanel}
        {tab === "stats" && <Panel className="p-4">{statsPanel}</Panel>}
      </div>

      <DragOverlay>{dragging ? <div className="w-24"><CardArt card={dragging} /></div> : null}</DragOverlay>
    </DndContext>
  );
}
