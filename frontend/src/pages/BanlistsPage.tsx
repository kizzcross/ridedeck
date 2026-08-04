import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Shield, ShieldCheck, Users } from "lucide-react";
import { banlistsApi, type BanlistListItem } from "@/api/banlists";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

function BanlistCard({ bl }: { bl: BanlistListItem }) {
  return (
    <Link to={`/app/banlists/${bl.uuid}`}>
      <Panel className="rd-card h-full p-4">
        <div className="mb-2 flex items-center gap-2">
          {bl.is_official ? <Badge tone="official">Official</Badge> : <Badge tone="community">Community</Badge>}
          <Badge tone="neutral">{bl.format_code}</Badge>
        </div>
        <h3 className="font-display line-clamp-1 text-sm">{bl.name}</h3>
        {bl.objective && <p className="mt-1 line-clamp-2 text-xs text-[var(--color-ink-muted)]">{bl.objective}</p>}
        <div className="mt-3 flex items-center gap-3 text-[11px] text-[var(--color-ink-subtle)]">
          <span>{bl.entry_count} regras</span>
          <span>♥ {bl.like_count}</span>
          {bl.owner && <span className="ml-auto">por {bl.owner.username}</span>}
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
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");

  const { data, isLoading } = useQuery({
    queryKey: ["banlists", tab],
    queryFn: () => banlistsApi.list({ category: tab }),
  });

  const create = useMutation({
    mutationFn: () => banlistsApi.create({ name: name || "Nova banlist", format_code: "standard" }),
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
        </div>
        <Button onClick={() => setCreating((s) => !s)}>
          <Plus className="h-4 w-4" /> Criar comunitária
        </Button>
      </div>

      {creating && (
        <Panel className="rd-fade-in flex flex-wrap items-end gap-3 p-4">
          <label className="flex-1">
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
          <Button loading={create.isPending} onClick={() => create.mutate()}>Criar e editar</Button>
        </Panel>
      )}

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

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-36" />)}
        </div>
      ) : (data?.results.length ?? 0) === 0 ? (
        <Panel className="p-10 text-center text-sm text-[var(--color-ink-muted)]">
          Nenhuma banlist {tab === "official" ? "oficial" : "comunitária"} ainda.
        </Panel>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data!.results.map((bl) => <BanlistCard key={bl.uuid} bl={bl} />)}
        </div>
      )}
    </div>
  );
}
