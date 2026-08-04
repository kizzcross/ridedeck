import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Layers, Plus, Globe, Lock, Link2 } from "lucide-react";
import { decksApi, type DeckListItem } from "@/api/decks";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

const VIS_ICON = { public: Globe, unlisted: Link2, private: Lock };

function DeckCard({ deck }: { deck: DeckListItem }) {
  const Icon = VIS_ICON[deck.visibility];
  return (
    <Link to={`/app/decks/${deck.uuid}`}>
      <Panel className="rd-card group flex h-full flex-col overflow-hidden">
        <div className="relative aspect-[16/7] overflow-hidden bg-[var(--color-surface-2)]">
          {deck.cover_image ? (
            <img src={deck.cover_image} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="grid h-full place-items-center">
              <Layers className="h-8 w-8 text-[var(--color-ink-subtle)]" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <Badge tone={deck.visibility === "public" ? "success" : "neutral"} className="absolute right-2 top-2">
            <Icon className="h-3 w-3" /> {deck.visibility}
          </Badge>
        </div>
        <div className="flex flex-1 flex-col p-3">
          <h3 className="font-display line-clamp-1 text-sm">{deck.title}</h3>
          <p className="font-display mt-0.5 text-[10px] uppercase text-[var(--color-ink-subtle)]">
            {deck.format_code} · {deck.main_count} cartas
          </p>
          <div className="mt-auto flex items-center gap-3 pt-2 text-[11px] text-[var(--color-ink-muted)]">
            <span>♥ {deck.like_count}</span>
            <span>★ {deck.favorite_count}</span>
          </div>
        </div>
      </Panel>
    </Link>
  );
}

export function MyDecksPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();
  const [title, setTitle] = useState("");
  const [format, setFormat] = useState("standard");
  const [creating, setCreating] = useState(false);

  const { data, isLoading } = useQuery({ queryKey: ["my-decks"], queryFn: decksApi.myDecks });

  const create = useMutation({
    mutationFn: () => decksApi.create({ title: title || "Novo deck", format_code: format }),
    onSuccess: (deck) => {
      qc.invalidateQueries({ queryKey: ["my-decks"] });
      navigate(`/app/decks/${deck.uuid}`);
    },
    onError: (e) => toast.error("Erro ao criar deck", apiErrorMessage(e)),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="font-display text-2xl"><span className="text-gradient">Meus Decks</span></h1>
          <p className="font-display text-[10px] uppercase tracking-wide text-[var(--color-ink-subtle)]">
            {data?.count ?? 0} decks
          </p>
        </div>
        <Button onClick={() => setCreating((s) => !s)}>
          <Plus className="h-4 w-4" /> Novo deck
        </Button>
      </div>

      {creating && (
        <Panel className="rd-fade-in flex flex-wrap items-end gap-3 p-4">
          <label className="flex-1">
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Nome</span>
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && create.mutate()}
              placeholder="Meu deck de Dragon Empire…"
              className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
              autoFocus
            />
          </label>
          <label>
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Formato</span>
            <select value={format} onChange={(e) => setFormat(e.target.value)}
              className="h-10 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm">
              <option value="standard">Standard</option>
              <option value="v_premium">V Premium</option>
              <option value="premium">Premium</option>
            </select>
          </label>
          <Button loading={create.isPending} onClick={() => create.mutate()}>Criar e abrir</Button>
        </Panel>
      )}

      {isLoading ? (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-52" />)}
        </div>
      ) : (data?.results.length ?? 0) === 0 ? (
        <Panel className="p-10 text-center">
          <Layers className="mx-auto mb-3 h-10 w-10 text-[var(--color-ink-subtle)]" />
          <p className="font-display">Nenhum deck ainda</p>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">Crie seu primeiro deck e comece a montar.</p>
        </Panel>
      ) : (
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
          {data!.results.map((d) => <DeckCard key={d.uuid} deck={d} />)}
        </div>
      )}
    </div>
  );
}
