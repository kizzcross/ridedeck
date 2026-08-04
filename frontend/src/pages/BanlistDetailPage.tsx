import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, GitFork, Layers, ShieldCheck, Trash2 } from "lucide-react";
import { banlistsApi } from "@/api/banlists";
import { cardsApi, type CardListItem } from "@/api/cards";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const RESTRICTIONS = [
  { code: "banned", label: "Banir", tone: "danger" as const },
  { code: "limit_to_1", label: "Limitar a 1", tone: "warning" as const },
  { code: "limit_to_2", label: "Limitar a 2", tone: "warning" as const },
  { code: "first_vanguard_forbidden", label: "First Vanguard proibido", tone: "neutral" as const },
];

function CardPicker({ onPick }: { onPick: (c: CardListItem) => void }) {
  const [raw, setRaw] = useState("");
  const search = useDebounce(raw, 300);
  const { data } = useQuery({
    queryKey: ["banlist-card-search", search],
    queryFn: () => cardsApi.list({ search, page_size: 8 }),
    enabled: search.length > 1,
  });
  return (
    <div>
      <input
        value={raw}
        onChange={(e) => setRaw(e.target.value)}
        placeholder="Buscar carta para restringir…"
        className="h-9 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
      />
      {data && data.results.length > 0 && (
        <ul className="mt-1 max-h-48 space-y-1 overflow-y-auto rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] p-1">
          {data.results.map((c) => (
            <li key={c.uuid}>
              <button
                onClick={() => { onPick(c); setRaw(""); }}
                className="flex w-full items-center gap-2 rounded-[4px] px-2 py-1 text-left text-sm hover:bg-[var(--color-surface-2)]"
              >
                <span className="font-display text-[10px] text-[var(--color-ink-subtle)]">G{c.grade}</span>
                <span className="truncate">{c.name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export function BanlistDetailPage() {
  const { uuid = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [restriction, setRestriction] = useState("banned");

  const { data: bl, isLoading } = useQuery({ queryKey: ["banlist", uuid], queryFn: () => banlistsApi.detail(uuid) });
  const refresh = () => qc.invalidateQueries({ queryKey: ["banlist", uuid] });

  const addEntry = useMutation({
    mutationFn: (card: string) => banlistsApi.addEntry(uuid, { restriction_type: restriction, card }),
    onSuccess: refresh,
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });
  const fork = useMutation({
    mutationFn: () => banlistsApi.fork(uuid),
    onSuccess: (b) => { toast.success("Fork criado!"); window.location.assign(`/app/banlists/${b.uuid}`); },
  });
  const makeOfficial = useMutation({
    mutationFn: () => banlistsApi.makeOfficial(uuid, !bl?.is_official),
    onSuccess: () => { refresh(); toast.success("Status oficial atualizado"); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  if (isLoading || !bl) return <Skeleton className="h-64 w-full" />;

  const entries = bl.current_version?.entries ?? [];
  const cardEntries = entries.filter((e) => e.card);
  const groupEntries = entries.filter((e) => e.group);

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Panel className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="mb-1 flex items-center gap-2">
              {bl.is_official ? <Badge tone="official">Official</Badge> : <Badge tone="community">Community</Badge>}
              <Badge tone="neutral">{bl.format_code}</Badge>
              <Badge tone="brand">v{bl.current_version?.version}</Badge>
            </div>
            <h1 className="font-display text-2xl">{bl.name}</h1>
            {bl.objective && <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{bl.objective}</p>}
            {bl.owner && <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">por {bl.owner.username}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="secondary" size="sm" loading={fork.isPending} onClick={() => fork.mutate()}>
              <GitFork className="h-4 w-4" /> Fork
            </Button>
            {user?.is_platform_admin && (
              <Button size="sm" onClick={() => makeOfficial.mutate()}>
                <ShieldCheck className="h-4 w-4" /> {bl.is_official ? "Remover oficial" : "Tornar oficial"}
              </Button>
            )}
          </div>
        </div>
      </Panel>

      {/* Owner editor */}
      {bl.is_owner && (
        <Panel className="space-y-3 p-4">
          <h3 className="font-display text-sm uppercase text-[var(--color-ink-muted)]">Adicionar restrição</h3>
          <div className="flex flex-wrap gap-1">
            {RESTRICTIONS.map((r) => (
              <button
                key={r.code}
                onClick={() => setRestriction(r.code)}
                className={cn(
                  "font-display rounded-[4px] border-2 px-3 py-1.5 text-[11px] uppercase",
                  restriction === r.code
                    ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                    : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
                )}
              >
                {r.label}
              </button>
            ))}
          </div>
          <CardPicker onPick={(c) => addEntry.mutate(c.uuid)} />
        </Panel>
      )}

      {/* Entries */}
      <Panel className="p-4">
        <h3 className="font-display mb-3 flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
          <Ban className="h-4 w-4" /> Restrições ({entries.length})
        </h3>
        {entries.length === 0 ? (
          <p className="text-sm text-[var(--color-ink-subtle)]">Nenhuma restrição ainda.</p>
        ) : (
          <ul className="space-y-1.5">
            {cardEntries.map((e) => (
              <li key={e.uuid} className="flex items-center gap-2 rounded-[6px] bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                <Badge tone={e.restriction_type === "banned" ? "danger" : "warning"}>
                  {e.restriction_type === "banned" ? "Banida" : `Limite ${e.effective_limit}`}
                </Badge>
                <span className="min-w-0 flex-1 truncate">{e.card!.name}</span>
                {bl.is_owner && (
                  <button
                    aria-label="Remover"
                    onClick={() => addEntryDelete(uuid, e.uuid, refresh)}
                    className="text-[var(--color-ink-subtle)] hover:text-[var(--color-danger)]"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                )}
              </li>
            ))}
          </ul>
        )}
      </Panel>

      {/* Choice restriction groups */}
      {groupEntries.length > 0 && (
        <Panel className="p-4">
          <h3 className="font-display mb-3 flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
            <Layers className="h-4 w-4" /> Grupos (Choice Restriction)
          </h3>
          <div className="space-y-3">
            {groupEntries.map((e) => (
              <div key={e.uuid} className="rounded-[6px] border-2 border-[var(--color-violet)]/40 bg-[var(--color-violet)]/5 p-3">
                <p className="font-display text-xs uppercase">{e.group!.name}</p>
                <p className="mb-2 text-[11px] text-[var(--color-ink-subtle)]">
                  {e.group!.kind === "choice"
                    ? "Escolha no máximo 1 destas cartas"
                    : e.group!.kind === "max_distinct"
                      ? `Máx ${e.group!.limit_value} identidades diferentes`
                      : `Máx ${e.group!.limit_value} cópias totais`}
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {e.group!.members.map((m) => (
                    <Badge key={m.uuid} tone="neutral">{m.card.name}</Badge>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </Panel>
      )}
    </div>
  );
}

async function addEntryDelete(uuid: string, entryUuid: string, refresh: () => void) {
  const { api } = await import("@/lib/api");
  await api.delete(`/banlists/${uuid}/entry/`, { data: { entry: entryUuid } });
  refresh();
}
