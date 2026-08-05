import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Ban, GitFork, Info, Layers, Plus, Save, Settings, ShieldCheck, Sparkles, Trash2, X } from "lucide-react";
import { banlistsApi, type BanlistDetail } from "@/api/banlists";
import { cardsApi, type CardListItem } from "@/api/cards";
import { useAuth } from "@/hooks/useAuth";
import { useDebounce } from "@/hooks/useDebounce";
import { Badge, Button, ConfirmDeleteDialog, Panel, Skeleton, useToast } from "@/components/ui";
import { CommentThread } from "@/components/CommentThread";
import { FORMATS, formatLabel } from "@/lib/formats";
import { CARD_RESTRICTIONS, GROUP_KINDS, RESTRICTION_META, type RestrictionTone } from "@/lib/banlistMeta";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

type Tone = RestrictionTone;

function CardPicker({ onPick, placeholder = "Buscar carta para restringir…" }: { onPick: (c: CardListItem) => void; placeholder?: string }) {
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
        placeholder={placeholder}
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

/** Builds a choice / max-distinct / max-total group — the feature that used to
 *  only be displayed, never created. */
function GroupBuilder({ uuid, onCreated }: { uuid: string; onCreated: () => void }) {
  const toast = useToast();
  const [kind, setKind] = useState("choice");
  const [name, setName] = useState("");
  const [limit, setLimit] = useState(1);
  const [members, setMembers] = useState<CardListItem[]>([]);

  const create = useMutation({
    mutationFn: () =>
      banlistsApi.addGroup(uuid, {
        name: name.trim() || "Grupo de escolha",
        kind,
        limit_value: kind === "choice" ? 1 : Math.max(1, limit),
        members: members.map((m) => m.uuid),
      }),
    onSuccess: () => {
      toast.success("Grupo criado");
      setName(""); setMembers([]); setLimit(1); setKind("choice");
      onCreated();
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const addMember = (c: CardListItem) => {
    setMembers((prev) => (prev.some((m) => m.uuid === c.uuid) ? prev : [...prev, c]));
  };

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-1">
        {Object.entries(GROUP_KINDS).map(([code, k]) => (
          <button
            key={code}
            onClick={() => setKind(code)}
            className={cn(
              "font-display rounded-[4px] border-2 px-3 py-1.5 text-[11px] uppercase",
              kind === code
                ? "border-[var(--color-border)] bg-[var(--color-violet)] text-white"
                : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
            )}
          >
            {k.label}
          </button>
        ))}
      </div>

      <p className="flex items-start gap-2 rounded-[6px] bg-[var(--color-violet)]/10 p-2.5 text-xs text-[var(--color-ink-muted)]">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--color-violet)]" />
        {GROUP_KINDS[kind].desc(Math.max(1, limit))}
      </p>

      <div className="flex flex-wrap gap-2">
        <input
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="Nome do grupo (ex.: Guardiões perfeitos)"
          className="h-9 min-w-0 flex-1 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
        />
        {kind !== "choice" && (
          <input
            type="number"
            min={1}
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value) || 1)}
            aria-label="Limite"
            className="h-9 w-20 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
          />
        )}
      </div>

      {members.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {members.map((m) => (
            <span key={m.uuid} className="flex items-center gap-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-xs">
              {m.name}
              <button aria-label="Remover" onClick={() => setMembers((p) => p.filter((x) => x.uuid !== m.uuid))}>
                <X className="h-3 w-3 text-[var(--color-ink-subtle)] hover:text-[var(--color-danger)]" />
              </button>
            </span>
          ))}
        </div>
      )}

      <CardPicker onPick={addMember} placeholder="Adicionar carta ao grupo…" />

      <Button size="sm" disabled={members.length < 2} loading={create.isPending} onClick={() => create.mutate()}>
        <Plus className="h-4 w-4" /> Criar grupo ({members.length})
      </Button>
      {members.length < 2 && (
        <p className="text-[11px] text-[var(--color-ink-subtle)]">Adicione pelo menos 2 cartas ao grupo.</p>
      )}
    </div>
  );
}

/** Owner-only settings: rename, change format, objective/description, visibility. */
function BanlistSettings({ bl, onSaved }: { bl: BanlistDetail; onSaved: () => void }) {
  const toast = useToast();
  const [name, setName] = useState(bl.name);
  const [format, setFormat] = useState(bl.format_code);
  const [objective, setObjective] = useState(bl.objective ?? "");
  const [description, setDescription] = useState(bl.description ?? "");
  const [isPublic, setIsPublic] = useState(bl.is_public);
  const [isListed, setIsListed] = useState(bl.is_listed);

  const save = useMutation({
    mutationFn: () =>
      banlistsApi.update(bl.uuid, {
        name: name.trim() || bl.name,
        format_code: format,
        objective,
        description,
        is_public: isPublic,
        is_listed: isListed,
      }),
    onSuccess: () => { toast.success("Banlist atualizada"); onSaved(); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const field = "h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm";
  const lbl = "font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]";

  return (
    <Panel className="space-y-3 p-4">
      <h3 className="font-display flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
        <Settings className="h-4 w-4" /> Configurações
      </h3>
      <div className="grid gap-3 sm:grid-cols-[1fr_12rem]">
        <label>
          <span className={lbl}>Nome</span>
          <input value={name} onChange={(e) => setName(e.target.value)} className={field} />
        </label>
        <label>
          <span className={lbl}>Formato</span>
          <select value={format} onChange={(e) => setFormat(e.target.value)} className={field}>
            {FORMATS.map((f) => <option key={f.code} value={f.code}>{f.label}</option>)}
          </select>
        </label>
      </div>
      {format !== bl.format_code && (
        <p className="flex items-start gap-2 rounded-[6px] bg-[var(--color-warning)]/10 p-2.5 text-xs text-[var(--color-ink-muted)]">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--color-warning)]" />
          Trocar o formato muda quais cartas são legais nos decks que usam esta banlist. As restrições já cadastradas continuam.
        </p>
      )}
      <label className="block">
        <span className={lbl}>Objetivo</span>
        <input value={objective} onChange={(e) => setObjective(e.target.value)} placeholder="Resumo curto do propósito" className={field} />
      </label>
      <label className="block">
        <span className={lbl}>Descrição</span>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          rows={3}
          placeholder="Explique as escolhas da banlist…"
          className="w-full resize-y rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2 text-sm"
        />
      </label>
      <div className="flex flex-wrap gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isPublic} onChange={(e) => setIsPublic(e.target.checked)} />
          Pública (outros podem ver pelo link)
        </label>
        <label className="flex items-center gap-2 text-sm">
          <input type="checkbox" checked={isListed} onChange={(e) => setIsListed(e.target.checked)} disabled={!isPublic} />
          Listada na comunidade
        </label>
      </div>
      <div className="flex justify-end">
        <Button size="sm" loading={save.isPending} onClick={() => save.mutate()}>
          <Save className="h-4 w-4" /> Salvar
        </Button>
      </div>
    </Panel>
  );
}

export function BanlistDetailPage() {
  const { uuid = "" } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [restriction, setRestriction] = useState("banned");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);

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
  const del = useMutation({
    mutationFn: () => banlistsApi.remove(uuid),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["banlists"] });
      toast.success("Banlist excluída");
      navigate("/app/banlists");
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });
  const delGroup = useMutation({
    mutationFn: (groupUuid: string) => banlistsApi.removeGroup(uuid, groupUuid),
    onSuccess: refresh,
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
            <div className="mb-1 flex flex-wrap items-center gap-2">
              {bl.is_official ? <Badge tone="official">Oficial</Badge> : <Badge tone="community">Comunidade</Badge>}
              <Badge tone="neutral">{formatLabel(bl.format_code)}</Badge>
              <Badge tone="brand">v{bl.current_version?.version}</Badge>
              {bl.is_owner && !bl.is_public && <Badge tone="warning">Privada</Badge>}
            </div>
            <h1 className="font-display text-2xl">{bl.name}</h1>
            {bl.objective && <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{bl.objective}</p>}
            {bl.owner && <p className="mt-1 text-xs text-[var(--color-ink-subtle)]">por {bl.owner.username}</p>}
          </div>
          <div className="flex flex-wrap gap-2">
            <a href={`/b/${uuid}`} target="_blank" rel="noreferrer">
              <Button variant="ghost" size="sm"><Sparkles className="h-4 w-4" /> Ver / exportar</Button>
            </a>
            <Button variant="secondary" size="sm" loading={fork.isPending} onClick={() => fork.mutate()}>
              <GitFork className="h-4 w-4" /> Fork
            </Button>
            {user?.is_platform_admin && (
              <Button size="sm" onClick={() => makeOfficial.mutate()}>
                <ShieldCheck className="h-4 w-4" /> {bl.is_official ? "Remover oficial" : "Tornar oficial"}
              </Button>
            )}
            {bl.is_owner && (
              <Button size="sm" variant={settingsOpen ? "secondary" : "ghost"} onClick={() => setSettingsOpen((s) => !s)}>
                <Settings className="h-4 w-4" /> Configurações
              </Button>
            )}
            {bl.is_owner && (
              <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="h-4 w-4" /> Excluir
              </Button>
            )}
          </div>
        </div>
      </Panel>

      {bl.is_owner && settingsOpen && (
        <BanlistSettings bl={bl} onSaved={() => { setSettingsOpen(false); refresh(); }} />
      )}

      <ConfirmDeleteDialog
        open={confirmDelete}
        title="Excluir banlist"
        description={`"${bl.name}" e todas as suas restrições serão removidas.`}
        loading={del.isPending}
        onConfirm={() => del.mutate()}
        onClose={() => setConfirmDelete(false)}
      />

      {/* Owner editors */}
      {bl.is_owner && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel className="space-y-3 p-4">
            <div>
              <h3 className="font-display text-sm uppercase text-[var(--color-ink-muted)]">Restringir uma carta</h3>
              <p className="text-xs text-[var(--color-ink-subtle)]">Escolha o tipo e busque a carta.</p>
            </div>
            <div className="flex flex-wrap gap-1">
              {CARD_RESTRICTIONS.map((code) => (
                <button
                  key={code}
                  onClick={() => setRestriction(code)}
                  className={cn(
                    "font-display rounded-[4px] border-2 px-3 py-1.5 text-[11px] uppercase",
                    restriction === code
                      ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                      : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
                  )}
                >
                  {RESTRICTION_META[code].label}
                </button>
              ))}
            </div>
            <p className="flex items-start gap-2 rounded-[6px] bg-[var(--color-surface-2)] p-2.5 text-xs text-[var(--color-ink-muted)]">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0 text-[var(--color-info)]" />
              {RESTRICTION_META[restriction]?.desc}
            </p>
            <CardPicker onPick={(c) => addEntry.mutate(c.uuid)} />
          </Panel>

          <Panel className="space-y-3 p-4">
            <div>
              <h3 className="font-display text-sm uppercase text-[var(--color-ink-muted)]">Grupo de escolha</h3>
              <p className="text-xs text-[var(--color-ink-subtle)]">
                Regra que vale para um conjunto de cartas juntas (ex.: “só pode usar 1 destas”).
              </p>
            </div>
            <GroupBuilder uuid={uuid} onCreated={refresh} />
          </Panel>
        </div>
      )}

      {/* Card restrictions */}
      <Panel className="p-4">
        <h3 className="font-display mb-3 flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
          <Ban className="h-4 w-4" /> Cartas restritas ({cardEntries.length})
        </h3>
        {cardEntries.length === 0 ? (
          <p className="text-sm text-[var(--color-ink-subtle)]">Nenhuma carta restrita ainda.</p>
        ) : (
          <ul className="space-y-1.5">
            {cardEntries.map((e) => {
              const meta = RESTRICTION_META[e.restriction_type] ?? { label: e.restriction_type, tone: "neutral" as Tone, desc: "" };
              return (
                <li key={e.uuid} className="flex items-center gap-3 rounded-[6px] bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                  <Badge tone={meta.tone}>{meta.label}</Badge>
                  <div className="min-w-0 flex-1">
                    <p className="truncate">{e.card!.name}</p>
                    {meta.desc && <p className="truncate text-[11px] text-[var(--color-ink-subtle)]">{meta.desc}</p>}
                  </div>
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
              );
            })}
          </ul>
        )}
      </Panel>

      {/* Choice / max groups */}
      {groupEntries.length > 0 && (
        <Panel className="p-4">
          <h3 className="font-display mb-1 flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
            <Layers className="h-4 w-4" /> Grupos de escolha ({groupEntries.length})
          </h3>
          <p className="mb-3 text-xs text-[var(--color-ink-subtle)]">
            Regras que valem para o conjunto de cartas abaixo, não para cada uma isolada.
          </p>
          <div className="space-y-3">
            {groupEntries.map((e) => {
              const k = GROUP_KINDS[e.group!.kind];
              return (
                <div key={e.uuid} className="rounded-[6px] border-2 border-[var(--color-violet)]/40 bg-[var(--color-violet)]/5 p-3">
                  <div className="mb-1 flex flex-wrap items-center gap-2">
                    <Badge tone="official">{k?.label ?? e.group!.kind}</Badge>
                    <p className="font-display text-xs uppercase">{e.group!.name}</p>
                    {bl.is_owner && (
                      <button
                        aria-label="Remover grupo"
                        onClick={() => delGroup.mutate(e.group!.uuid)}
                        className="ml-auto text-[var(--color-ink-subtle)] hover:text-[var(--color-danger)]"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                  <p className="mb-2 text-[11px] text-[var(--color-ink-muted)]">{k?.desc(e.group!.limit_value)}</p>
                  <div className="flex flex-wrap gap-1.5">
                    {e.group!.members.map((m) => (
                      <Badge key={m.uuid} tone="neutral">{m.card.name}</Badge>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
        </Panel>
      )}

      <CommentThread targetType="banlist" targetUuid={uuid} />
    </div>
  );
}

async function addEntryDelete(uuid: string, entryUuid: string, refresh: () => void) {
  const { api } = await import("@/lib/api");
  await api.delete(`/banlists/${uuid}/entry/`, { data: { entry: entryUuid } });
  refresh();
}
