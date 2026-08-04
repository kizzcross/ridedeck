import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, History, Search, ShieldCheck } from "lucide-react";
import { powerApi, type AdminCardRow } from "@/api/powerlevel";
import { useDebounce } from "@/hooks/useDebounce";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const LEVELS = Array.from({ length: 10 }, (_, i) => i + 1);
const FORMATS = [
  { code: "standard", label: "Standard" },
  { code: "v_premium", label: "V Premium" },
  { code: "g", label: "G Era" },
  { code: "premium", label: "Premium" },
];

function levelColor(v: number | null): string {
  if (v == null) return "var(--color-ink-subtle)";
  if (v >= 9) return "var(--color-danger)";
  if (v >= 7) return "var(--color-warning)";
  if (v >= 5) return "var(--color-accent)";
  return "var(--color-success)";
}

export function PowerLevelAdminPage() {
  const toast = useToast();
  const qc = useQueryClient();
  const [format, setFormat] = useState("standard");
  const [raw, setRaw] = useState("");
  const search = useDebounce(raw, 300);
  const [unrated, setUnrated] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [value, setValue] = useState(5);
  const [justification, setJustification] = useState("");
  const [historyCard, setHistoryCard] = useState<string | null>(null);

  const { data, isLoading } = useQuery({
    queryKey: ["admin-power-cards", format, search, unrated],
    queryFn: () => powerApi.adminCards({ format_code: format, search, unrated: unrated ? "1" : undefined }),
  });
  const rows = data?.results ?? [];

  const { data: history } = useQuery({
    queryKey: ["power-history", historyCard, format],
    queryFn: () => powerApi.history(historyCard!, format),
    enabled: !!historyCard,
  });

  const refresh = () => qc.invalidateQueries({ queryKey: ["admin-power-cards"] });

  const single = useMutation({
    mutationFn: (card: string) => powerApi.setLevel({ card, format_code: format, value, justification }),
    onSuccess: () => { refresh(); toast.success("Power level definido"); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const bulk = useMutation({
    mutationFn: () => powerApi.bulkSet({ cards: [...selected], format_code: format, value, justification }),
    onSuccess: (d) => { refresh(); setSelected(new Set()); toast.success(`${d.updated} cartas atualizadas`); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const toggle = (uuid: string) =>
    setSelected((s) => {
      const n = new Set(s);
      n.has(uuid) ? n.delete(uuid) : n.add(uuid);
      return n;
    });

  const canSubmit = justification.trim().length >= 3;
  const selectedRows = useMemo(() => rows.filter((r) => selected.has(r.uuid)), [rows, selected]);

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="font-display flex items-center gap-2 text-2xl">
            <ShieldCheck className="h-6 w-6 text-[var(--color-violet)]" />
            <span className="text-gradient">Power Level</span>
          </h1>
          <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
            Editor editorial — somente Platform Admin
          </p>
        </div>
        <select
          value={format}
          onChange={(e) => setFormat(e.target.value)}
          className="h-10 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
        >
          {FORMATS.map((f) => <option key={f.code} value={f.code}>{f.label}</option>)}
        </select>
      </div>

      {/* Edit controls */}
      <Panel className="space-y-3 p-4">
        <div className="grid gap-3 md:grid-cols-[auto_1fr]">
          <div>
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Novo nível</span>
            <div className="flex flex-wrap gap-1">
              {LEVELS.map((l) => (
                <button
                  key={l}
                  onClick={() => setValue(l)}
                  className={cn(
                    "font-display h-9 w-9 rounded-[4px] border-2 text-sm",
                    value === l ? "border-[var(--color-ink)]" : "border-[var(--color-border)]",
                  )}
                  style={{ background: value === l ? levelColor(l) : "var(--color-surface-2)", color: value === l ? "#140f00" : "var(--color-ink-muted)" }}
                >
                  {l}
                </button>
              ))}
            </div>
          </div>
          <div>
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">
              Justificativa (obrigatória)
            </span>
            <textarea
              value={justification}
              onChange={(e) => setJustification(e.target.value)}
              rows={2}
              placeholder="Motivo da avaliação…"
              className="w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm focus:border-[var(--color-accent)]"
            />
          </div>
        </div>

        {selected.size > 0 && (
          <div className="rd-fade-in flex flex-wrap items-center gap-3 rounded-[var(--radius-card)] border-2 border-[var(--color-violet)]/40 bg-[var(--color-violet)]/10 p-3">
            <AlertTriangle className="h-5 w-5 text-[var(--color-violet)]" />
            <div className="flex-1 text-sm">
              <b>{selected.size} cartas</b> serão definidas para nível <b>{value}</b> em <b>{format}</b>.
              <span className="ml-1 text-[var(--color-ink-muted)]">Valores anteriores serão registrados na auditoria.</span>
            </div>
            <Button variant="secondary" size="sm" onClick={() => setSelected(new Set())}>Limpar</Button>
            <Button size="sm" loading={bulk.isPending} disabled={!canSubmit} onClick={() => bulk.mutate()}>
              Aplicar em lote ({selected.size})
            </Button>
          </div>
        )}
        {selectedRows.length > 0 && (
          <p className="text-[11px] text-[var(--color-ink-subtle)]">
            Preview: {selectedRows.slice(0, 6).map((r) => r.name).join(", ")}
            {selectedRows.length > 6 ? `… +${selectedRows.length - 6}` : ""}
          </p>
        )}
      </Panel>

      {/* Search / filters */}
      <div className="flex flex-wrap gap-2">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--color-ink-subtle)]" />
          <input
            value={raw}
            onChange={(e) => setRaw(e.target.value)}
            placeholder="Buscar cartas…"
            className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] pl-9 pr-3 text-sm"
          />
        </div>
        <Button variant={unrated ? "primary" : "outline"} onClick={() => setUnrated((v) => !v)}>
          Sem avaliação
        </Button>
      </div>

      {/* Card table */}
      <Panel className="overflow-hidden">
        {isLoading ? (
          <div className="space-y-2 p-3">{Array.from({ length: 6 }).map((_, i) => <Skeleton key={i} className="h-12" />)}</div>
        ) : (
          <ul className="divide-y-2 divide-[var(--color-border)]">
            {rows.map((r: AdminCardRow) => (
              <li key={r.uuid} className="flex items-center gap-3 px-3 py-2">
                <input
                  type="checkbox"
                  checked={selected.has(r.uuid)}
                  onChange={() => toggle(r.uuid)}
                  aria-label={`Selecionar ${r.name}`}
                  className="h-4 w-4 accent-[var(--color-accent)]"
                />
                {r.image ? (
                  <img src={r.image} alt="" className="h-10 w-7 rounded-[3px] object-cover" loading="lazy" />
                ) : (
                  <div className="h-10 w-7 rounded-[3px] bg-[var(--color-surface-2)]" />
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{r.name}</p>
                  <p className="font-display text-[9px] uppercase text-[var(--color-ink-subtle)]">
                    G{r.grade}{r.clan ? ` · ${r.clan}` : ""}
                  </p>
                </div>
                {r.power_value != null ? (
                  <span className="font-display grid h-8 w-8 place-items-center rounded-[4px] border-2 border-[var(--color-border)] text-sm text-[#140f00]"
                    style={{ background: levelColor(r.power_value) }}
                    title={`Nível atual: ${r.power_value} (${r.power_status})`}>
                    {r.power_value}
                  </span>
                ) : (
                  <Badge tone="warning">sem nível</Badge>
                )}
                <Button size="sm" variant="secondary" disabled={!canSubmit} onClick={() => single.mutate(r.uuid)}>
                  → {value}
                </Button>
                <Button size="icon" variant="ghost" aria-label="Histórico" onClick={() => setHistoryCard(r.uuid)}>
                  <History className="h-4 w-4" />
                </Button>
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {/* History drawer (inline) */}
      {historyCard && (
        <Panel className="p-4">
          <div className="mb-2 flex items-center justify-between">
            <h3 className="font-display text-sm uppercase">Histórico de auditoria</h3>
            <Button size="sm" variant="ghost" onClick={() => setHistoryCard(null)}>Fechar</Button>
          </div>
          {history && history.length > 0 ? (
            <ul className="space-y-1.5">
              {history.map((h, i) => (
                <li key={i} className="rounded-[6px] bg-[var(--color-surface-2)] px-3 py-2 text-xs">
                  <span className="font-display">{h.previous_value ?? "—"} → {h.new_value}</span>
                  <span className="ml-2 text-[var(--color-ink-muted)]">v{h.version} · {h.source} · {h.admin}</span>
                  {h.justification && <p className="mt-0.5 text-[var(--color-ink-subtle)]">“{h.justification}”</p>}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-ink-subtle)]">Sem histórico para este formato.</p>
          )}
        </Panel>
      )}
    </div>
  );
}
