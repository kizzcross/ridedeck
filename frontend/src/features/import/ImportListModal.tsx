import { useEffect, useMemo, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AlertTriangle, CheckCircle2, HelpCircle, Upload, X } from "lucide-react";
import { decksApi, type ImportCard, type ImportLine, type Zone } from "@/api/decks";
import { banlistsApi, type ImportBanEntry } from "@/api/banlists";
import { Button, useToast } from "@/components/ui";
import { useReduceMotion } from "@/app/MotionProvider";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const ZONE_LABEL: Record<Zone, string> = { main_deck: "Main", ride_deck: "Ride", g_deck: "G" };
const RESTRICTION_OPTS = [
  { v: "banned", label: "Banida" },
  { v: "limit_to_1", label: "Limite 1" },
  { v: "limit_to_2", label: "Limite 2" },
];
const HINT_DECK =
  "Cole a lista, um card por linha. Aceita: “4x Nome”, “4 Nome”, “Nome x4”, “Nome (BT01/001)”, só o nome, CSV… e cabeçalhos de zona (Main / Ride / G).";
const HINT_BAN =
  "Um card por linha. O número é o limite: “0 Nome” = banida, “1 Nome” = limite 1, “2 Nome” = limite 2. Aceita cabeçalhos (Banidas / Limite 1) e “Nome — banida”.";

type Row = {
  key: string;
  inputName: string;
  quantity: number;
  zone: Zone;
  confidence: string;
  chosen: string;              // selected card uuid ("" = ignore)
  options: ImportCard[];       // matched + suggestions (deduped)
  restriction?: string;        // banlist only
};

function optionsOf(card: ImportCard | null, suggestions: ImportCard[]): ImportCard[] {
  const all = [card, ...suggestions].filter(Boolean) as ImportCard[];
  const seen = new Set<string>();
  return all.filter((c) => (seen.has(c.uuid) ? false : (seen.add(c.uuid), true)));
}

/** Paste-a-list importer for decks and banlists. Resolves each line to a card
 *  (fuzzy — tolerant of typos) and lets the user fix any uncertain match before
 *  applying. Same component, two modes. */
export function ImportListModal({
  open,
  kind,
  targetUuid,
  onClose,
  onApplied,
}: {
  open: boolean;
  kind: "deck" | "banlist";
  targetUuid: string;
  onClose: () => void;
  onApplied: () => void;
}) {
  const reduce = useReduceMotion();
  const toast = useToast();
  const [text, setText] = useState("");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [replace, setReplace] = useState(false);
  const [loading, setLoading] = useState(false);

  // Start fresh every time the modal opens (never show a stale preview). Resetting
  // on open — not on close — avoids a content flash during the exit animation.
  useEffect(() => {
    if (open) {
      setText("");
      setRows(null);
      setReplace(false);
    }
  }, [open]);

  const runPreview = async () => {
    setLoading(true);
    try {
      if (kind === "deck") {
        const lines: ImportLine[] = await decksApi.importPreview(text);
        setRows(lines.map((l, i) => ({
          key: `${i}-${l.raw}`, inputName: l.input_name, quantity: l.quantity, zone: l.zone,
          confidence: l.confidence, chosen: l.card?.uuid ?? "", options: optionsOf(l.card, l.suggestions),
        })));
      } else {
        const entries: ImportBanEntry[] = await banlistsApi.importPreview(text);
        setRows(entries.map((e, i) => ({
          key: `${i}-${e.raw}`, inputName: e.input_name, quantity: 1, zone: "main_deck",
          confidence: e.confidence, chosen: e.card?.uuid ?? "", options: optionsOf(e.card, e.suggestions),
          restriction: e.restriction_type,
        })));
      }
    } catch (e) {
      toast.error("Não deu pra ler a lista", apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  const counts = useMemo(() => {
    const r = rows ?? [];
    return {
      ok: r.filter((x) => x.chosen && ["exact", "code", "fuzzy"].includes(x.confidence)).length,
      review: r.filter((x) => x.chosen && x.confidence === "ambiguous").length,
      missing: r.filter((x) => !x.chosen).length,
    };
  }, [rows]);

  const setRow = (key: string, patch: Partial<Row>) =>
    setRows((rs) => (rs ?? []).map((r) => (r.key === key ? { ...r, ...patch } : r)));

  const apply = async () => {
    if (!rows) return;
    setLoading(true);
    try {
      const chosen = rows.filter((r) => r.chosen);
      if (kind === "deck") {
        await decksApi.importApply(targetUuid,
          chosen.map((r) => ({ card: r.chosen, zone: r.zone, quantity: r.quantity })), replace);
      } else {
        await banlistsApi.importApply(targetUuid,
          chosen.map((r) => ({ card: r.chosen, restriction_type: r.restriction ?? "banned", limit_value: null })), replace);
      }
      toast.success(`Importado! ${chosen.length} ${kind === "deck" ? "cards" : "restrições"}.`);
      onApplied();
      onClose();   // state is reset on the next open (see effect above)
    } catch (e) {
      toast.error("Erro ao importar", apiErrorMessage(e));
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/70 p-4 backdrop-blur-sm"
          initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} onClick={onClose}
        >
          <motion.div
            className="my-8 w-full max-w-2xl rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] shadow-hard"
            initial={reduce ? false : { y: 16, opacity: 0 }} animate={{ y: 0, opacity: 1 }} exit={reduce ? undefined : { y: 16, opacity: 0 }}
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center gap-2 border-b-2 border-[var(--color-border)] p-4">
              <Upload className="h-5 w-5 text-[var(--color-accent)]" />
              <h2 className="font-display text-lg">Importar {kind === "deck" ? "deck" : "banlist"} por lista</h2>
              <button onClick={onClose} aria-label="Fechar" className="ml-auto text-[var(--color-ink-subtle)] hover:text-[var(--color-ink)]"><X className="h-5 w-5" /></button>
            </div>

            <div className="space-y-4 p-4">
              {!rows ? (
                <>
                  <p className="flex items-start gap-2 text-[13px] leading-relaxed text-[var(--color-ink-muted)]">
                    <HelpCircle className="mt-0.5 h-4 w-4 shrink-0 text-[var(--color-violet)]" />
                    {kind === "deck" ? HINT_DECK : HINT_BAN}
                  </p>
                  <textarea
                    value={text} onChange={(e) => setText(e.target.value)} autoFocus rows={10}
                    placeholder={kind === "deck" ? "4x Dragonic Overlord\n4 Blaster Blade\nChronojet Dragon x2…" : "Banidas\nDragonic Overlord\nLimite 1\nBlaster Blade…"}
                    className="w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] p-3 font-mono text-sm"
                  />
                  <div className="flex justify-end">
                    <Button loading={loading} disabled={!text.trim()} onClick={runPreview}>Ver prévia</Button>
                  </div>
                </>
              ) : (
                <>
                  {/* Summary */}
                  <div className="flex flex-wrap gap-3 text-xs">
                    <span className="flex items-center gap-1 text-[var(--color-success)]"><CheckCircle2 className="h-4 w-4" /> {counts.ok} reconhecidas</span>
                    {counts.review > 0 && <span className="flex items-center gap-1 text-[var(--color-warning)]"><AlertTriangle className="h-4 w-4" /> {counts.review} confira</span>}
                    {counts.missing > 0 && <span className="flex items-center gap-1 text-[var(--color-danger)]"><X className="h-4 w-4" /> {counts.missing} não encontradas</span>}
                  </div>

                  <div className="max-h-[46vh] space-y-1.5 overflow-y-auto pr-1">
                    {rows.map((r) => {
                      const img = r.options.find((o) => o.uuid === r.chosen)?.default_printing?.image_url;
                      const tone = !r.chosen ? "danger" : r.confidence === "ambiguous" ? "warning" : "success";
                      return (
                        <div key={r.key} className={cn("flex items-center gap-2 rounded-[6px] border-2 bg-[var(--color-surface-2)] p-2",
                          tone === "danger" ? "border-[var(--color-danger)]/40" : tone === "warning" ? "border-[var(--color-warning)]/40" : "border-[var(--color-border)]")}>
                          {kind === "deck" ? (
                            <span className="font-display grid h-7 w-7 shrink-0 place-items-center rounded-[4px] bg-[var(--color-surface-3)] text-xs">{r.quantity}</span>
                          ) : (
                            <select value={r.restriction} onChange={(e) => setRow(r.key, { restriction: e.target.value })}
                              className="h-7 shrink-0 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-1 text-[11px]">
                              {RESTRICTION_OPTS.map((o) => <option key={o.v} value={o.v}>{o.label}</option>)}
                            </select>
                          )}
                          {img ? <img src={img} alt="" className="h-9 w-7 shrink-0 rounded-[3px] object-cover" /> : <span className="h-9 w-7 shrink-0 rounded-[3px] bg-[var(--color-surface-3)]" />}
                          <div className="min-w-0 flex-1">
                            <select value={r.chosen} onChange={(e) => setRow(r.key, { chosen: e.target.value })}
                              className="w-full rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 py-1 text-sm">
                              <option value="">— ignorar “{r.inputName}” —</option>
                              {r.options.map((c) => <option key={c.uuid} value={c.uuid}>{c.name}</option>)}
                            </select>
                            {r.chosen && r.confidence !== "exact" && r.confidence !== "code" && (
                              <p className="mt-0.5 pl-1 text-[10px] text-[var(--color-ink-subtle)]">de “{r.inputName}”{r.confidence === "ambiguous" ? " · confira se é isso" : " · corrigido"}</p>
                            )}
                          </div>
                          {kind === "deck" && (
                            <span className="font-display shrink-0 text-[9px] uppercase text-[var(--color-ink-subtle)]">{ZONE_LABEL[r.zone]}</span>
                          )}
                        </div>
                      );
                    })}
                  </div>

                  <div className="flex flex-wrap items-center justify-between gap-3 border-t-2 border-[var(--color-border)] pt-3">
                    <label className="flex cursor-pointer items-center gap-2 text-xs text-[var(--color-ink-muted)]">
                      <input type="checkbox" checked={replace} onChange={(e) => setReplace(e.target.checked)} className="accent-[var(--color-accent)]" />
                      Substituir o conteúdo atual (em vez de adicionar)
                    </label>
                    <div className="flex gap-2">
                      <Button variant="ghost" onClick={() => setRows(null)}>Voltar</Button>
                      <Button loading={loading} disabled={counts.ok + counts.review === 0} onClick={apply}>
                        Importar {counts.ok + counts.review}
                      </Button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
