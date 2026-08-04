import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { decksApi, type DeckDetail, type DeckEntry, type Zone } from "@/api/decks";
import type { CardListItem } from "@/api/cards";
import { useDebounce } from "@/hooks/useDebounce";

type SaveState = "idle" | "saving" | "saved" | "error";

interface HistoryOp {
  cardUuid: string;
  zone: Zone;
  prevQty: number;
  nextQty: number;
}

/** Manages the editable deck: optimistic entries, per-change persistence
 *  (autosave), undo/redo, and debounced validation. */
export function useDeckBuilder(deckUuid: string) {
  const { data: deck, isLoading, refetch } = useQuery({
    queryKey: ["deck", deckUuid],
    queryFn: () => decksApi.detail(deckUuid),
  });

  const [entries, setEntries] = useState<DeckEntry[]>([]);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const undoStack = useRef<HistoryOp[]>([]);
  const redoStack = useRef<HistoryOp[]>([]);
  const [, force] = useState(0);
  const bump = () => force((n) => n + 1);

  useEffect(() => {
    if (deck?.current_version) setEntries(deck.current_version.entries);
  }, [deck?.current_version]);

  const qtyOf = useCallback(
    (cardUuid: string, zone: Zone) =>
      entries.find((e) => e.card.uuid === cardUuid && e.zone === zone)?.quantity ?? 0,
    [entries],
  );

  const persist = useCallback(
    async (card: CardListItem, zone: Zone, quantity: number) => {
      setSaveState("saving");
      try {
        const version = await decksApi.setEntry(deckUuid, { card: card.uuid, zone, quantity });
        setEntries(version.entries);
        setSaveState("saved");
      } catch {
        setSaveState("error");
      }
    },
    [deckUuid],
  );

  const applyOp = useCallback(
    (card: CardListItem, zone: Zone, nextQty: number, record = true) => {
      const prevQty = qtyOf(card.uuid, zone);
      const clamped = Math.max(0, Math.min(99, nextQty));
      if (clamped === prevQty) return;
      // optimistic local update
      setEntries((prev) => {
        const rest = prev.filter((e) => !(e.card.uuid === card.uuid && e.zone === zone));
        if (clamped === 0) return rest;
        const existing = prev.find((e) => e.card.uuid === card.uuid && e.zone === zone);
        return [
          ...rest,
          existing
            ? { ...existing, quantity: clamped }
            : { uuid: `tmp-${card.uuid}-${zone}`, card, zone, quantity: clamped, preferred_printing: null },
        ];
      });
      if (record) {
        undoStack.current.push({ cardUuid: card.uuid, zone, prevQty, nextQty: clamped });
        redoStack.current = [];
        bump();
      }
      void persist(card, zone, clamped);
    },
    [persist, qtyOf],
  );

  const add = useCallback((card: CardListItem, zone: Zone) => applyOp(card, zone, qtyOf(card.uuid, zone) + 1), [applyOp, qtyOf]);
  const decrement = useCallback((card: CardListItem, zone: Zone) => applyOp(card, zone, qtyOf(card.uuid, zone) - 1), [applyOp, qtyOf]);
  const setQty = useCallback((card: CardListItem, zone: Zone, q: number) => applyOp(card, zone, q), [applyOp]);
  const removeAll = useCallback((card: CardListItem, zone: Zone) => applyOp(card, zone, 0), [applyOp]);

  const cardByUuid = useCallback(
    (uuid: string) => entries.find((e) => e.card.uuid === uuid)?.card,
    [entries],
  );

  const undo = useCallback(() => {
    const op = undoStack.current.pop();
    if (!op) return;
    const card = cardByUuid(op.cardUuid);
    if (!card) return;
    redoStack.current.push(op);
    applyOp(card, op.zone, op.prevQty, false);
    bump();
  }, [applyOp, cardByUuid]);

  const redo = useCallback(() => {
    const op = redoStack.current.pop();
    if (!op) return;
    const card = cardByUuid(op.cardUuid);
    if (!card) return;
    undoStack.current.push(op);
    applyOp(card, op.zone, op.nextQty, false);
    bump();
  }, [applyOp, cardByUuid]);

  // keyboard shortcuts
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "z") {
        e.preventDefault();
        if (e.shiftKey) redo();
        else undo();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [undo, redo]);

  const zoneCounts = useMemo(() => {
    const c: Record<Zone, number> = { main_deck: 0, ride_deck: 0, g_deck: 0 };
    entries.forEach((e) => (c[e.zone] += e.quantity));
    return c;
  }, [entries]);

  // Debounced validation whenever entries change.
  const validationKey = useDebounce(JSON.stringify(zoneCounts) + entries.length, 400);
  const { data: validation } = useQuery({
    queryKey: ["deck-validate", deckUuid, validationKey],
    queryFn: () => decksApi.validate(deckUuid),
    enabled: !!deck,
  });

  return {
    deck: deck as DeckDetail | undefined,
    isLoading,
    entries,
    zoneCounts,
    saveState,
    validation,
    qtyOf,
    add,
    decrement,
    setQty,
    removeAll,
    undo,
    redo,
    canUndo: undoStack.current.length > 0,
    canRedo: redoStack.current.length > 0,
    refetch,
  };
}
