import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Shield, ShieldCheck, Users } from "lucide-react";
import { banlistsApi, type BanlistListItem } from "@/api/banlists";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { FORMATS, formatLabel } from "@/lib/formats";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

function BanlistCard({ bl }: { bl: BanlistListItem }) {
  return (
    <Link to={`/app/banlists/${bl.uuid}`}>
      <Panel className="rd-card h-full p-4 transition-transform hover:-translate-y-0.5">
        <div className="mb-2 flex items-center gap-2">
          {bl.is_official ? <Badge tone="official">Oficial</Badge> : <Badge tone="community">Comunidade</Badge>}
          <Badge tone="neutral">{formatLabel(bl.format_code)}</Badge>
        </div>
        <h3 className="font-display line-clamp-1 text-sm">{bl.name}</h3>
        {bl.objective && <p className="mt-1 line-clamp-2 text-xs text-[var(--color-ink-muted)]">{bl.objective}</p>}
        <div className="mt-3 flex items-center gap-3 text-[11px] text-[var(--color-ink-subtle)]">
          <span>{bl.entry_count} regras</span>
          <span>♥ {bl.like_count}</span>
          {bl.owner && <span className="ml-auto truncate">por {bl.owner.username}</span>}
        </div>
      </Panel>
    </Link>
  );
}

export function BanlistsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();
  const [tab, setTab] = useState<"official" | "community">("official");
  const [formatFilter, setFormatFilter] = useState<string>("");
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [format, setFormat] = useState("standard");
  const [objective, setObjective] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["banlists", tab, formatFilter],
    queryFn: () => banlistsApi.list({ category: tab, ...(formatFilter ? { format_code: formatFilter } : {}) }),
  });

  const create = useMutation({
    mutationFn: () => banlistsApi.create({ name: name.trim() || "Nova banlist", format_code: format, objective: objective.trim() }),
    onSuccess: (bl) => {
      qc.invalidateQueries({ queryKey: ["banlists"] });
      navigate(`/app/banlists/${bl.uuid}`);
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display flex items-center gap-2 text-2xl">
            <Shield className="h-6 w-6 text-[var(--color-violet)]" />
            <span className="text-gradient">Banlists</span>
          </h1>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Regras de banimento e limite por formato. Escolha uma ao validar seus decks.
          </p>
        </div>
        <Button onClick={() => setCreating((s) => !s)}>
          <Plus className="h-4 w-4" /> Nova banlist
        </Button>
      </div>

      {creating && (
        <Panel className="rd-fade-in space-y-3 p-4">
          <div className="grid gap-3 sm:grid-cols-[1fr_10rem]">
            <label>
              <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Nome</span>
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && create.mutate()}
                placeholder="Minha banlist casual…"
                autoFocus
                className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              />
            </label>
            <label>
              <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Formato</span>
              <select
                value={format}
                onChange={(e) => setFormat(e.target.value)}
                className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              >
                {FORMATS.map((f) => <option key={f.code} value={f.code}>{f.label}</option>)}
              </select>
            </label>
          </div>
          <label className="block">
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Objetivo (opcional)</span>
            <input
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && create.mutate()}
              placeholder="Ex.: formato equilibrado, sem decks de FTK…"
              className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
            />
          </label>
          <div className="flex justify-end gap-2">
            <Button variant="ghost" onClick={() => setCreating(false)}>Cancelar</Button>
            <Button loading={create.isPending} onClick={() => create.mutate()}>Criar e editar</Button>
          </div>
        </Panel>
      )}

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="flex gap-1">
          {([["official", "Oficiais", ShieldCheck], ["community", "Comunidade", Users]] as const).map(([key, label, Icon]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={cn(
                "font-display flex items-center gap-2 rounded-[var(--radius-card)] border-2 px-4 py-2 text-xs uppercase",
                tab === key
                  ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
              )}
            >
              <Icon className="h-4 w-4" /> {label}
            </button>
          ))}
        </div>
        <div className="ml-auto flex flex-wrap gap-1">
          {[{ code: "", label: "Todos" }, ...FORMATS].map((f) => (
            <button
              key={f.code || "all"}
              onClick={() => setFormatFilter(f.code)}
              className={cn(
                "font-display rounded-[4px] border-2 px-2.5 py-1.5 text-[11px] uppercase",
                formatFilter === f.code
                  ? "border-[var(--color-border)] bg-[var(--color-violet)] text-white"
                  : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
              )}
            >
              {f.label}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-36" />)}
        </div>
      ) : (data?.results.length ?? 0) === 0 ? (
        <Panel className="p-10 text-center text-sm text-[var(--color-ink-muted)]">
          Nenhuma banlist {tab === "official" ? "oficial" : "comunitária"}
          {formatFilter ? ` de ${formatLabel(formatFilter)}` : ""} ainda.
        </Panel>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data!.results.map((bl) => <BanlistCard key={bl.uuid} bl={bl} />)}
        </div>
      )}
    </div>
  );
}
