import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Library, Layers, Shield, Swords, ArrowRight, Plus, Play,
  Heart, Users, LayoutGrid, Flame, Sparkles, Wrench,
} from "lucide-react";
import { decksApi } from "@/api/decks";
import { collectionApi } from "@/api/collection";
import { socialApi } from "@/api/social";
import { useAuth } from "@/hooks/useAuth";
import { Avatar } from "@/components/Avatar";
import { NationLogo } from "@/components/NationLogo";
import { Button, Panel, Skeleton, useToast } from "@/components/ui";
import { nationLabel } from "@/lib/cardMeta";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const MENU = [
  { to: "/app/cards", icon: Library, title: "Cartas", desc: "Vasculhe o catálogo e ache combos", tint: "var(--color-info)" },
  { to: "/app/decks", icon: Layers, title: "Decks", desc: "Construa e afine no builder", tint: "var(--color-accent)" },
  { to: "/app/banlists", icon: Shield, title: "Banlists", desc: "Regras oficiais e da comunidade", tint: "var(--color-violet)" },
  { to: "/app/tournaments", icon: Swords, title: "Torneios", desc: "Entre na arena e dispute", tint: "var(--color-danger)" },
];

function Stat({ icon: Icon, label, value, tint }: { icon: typeof Heart; label: string; value: number | string; tint: string }) {
  return (
    <div className="rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5">
      <Icon className="h-4 w-4" style={{ color: tint }} />
      <p className="font-display mt-1.5 text-2xl leading-none">{value}</p>
      <p className="mt-1 text-[11px] uppercase tracking-wide text-[var(--color-ink-subtle)]">{label}</p>
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const qc = useQueryClient();
  const toast = useToast();

  const decksQ = useQuery({ queryKey: ["decks", "mine"], queryFn: () => decksApi.myDecks() });
  const summaryQ = useQuery({ queryKey: ["collection", "summary"], queryFn: () => collectionApi.summary() });
  const favQ = useQuery({ queryKey: ["favorites", "mine"], queryFn: () => socialApi.favorites() });
  const feedQ = useQuery({
    queryKey: ["decks", "hot"],
    queryFn: () => decksApi.publicDecks({ ordering: "-like_count", page_size: 6 }),
  });

  const create = useMutation({
    mutationFn: () => decksApi.create({ title: "Novo deck", format_code: "standard" }),
    onSuccess: (deck) => {
      qc.invalidateQueries({ queryKey: ["decks"] });
      navigate(`/app/decks/${deck.uuid}`);
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const myDecks = decksQ.data;
  const lastDeck = myDecks?.results?.[0];
  const deckCount = myDecks?.count ?? myDecks?.results?.length ?? 0;
  const cardsCount = summaryQ.data?.total_cards ?? 0;
  const favCount = favQ.data?.count ?? 0;
  const feed = feedQ.data?.results ?? [];

  return (
    <div className="space-y-6">
      {/* Greeting */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-display text-xs uppercase tracking-[0.2em] text-[var(--color-accent)]">RideDeck</p>
          <h1 className="font-display mt-1 text-3xl">Salve, {user?.username}</h1>
          <p className="mt-1 text-[var(--color-ink-muted)]">
            Bora montar o próximo deck campeão? O Circuito não espera.
          </p>
        </div>
        <Button onClick={() => create.mutate()} loading={create.isPending}>
          <Plus className="h-4 w-4" /> Montar deck
        </Button>
      </div>

      {/* Player card */}
      <Panel className="relative overflow-hidden p-5">
        <div
          className="pointer-events-none absolute -right-16 -top-16 h-52 w-52 rounded-full opacity-20 blur-2xl"
          style={{ background: "var(--color-accent)" }}
          aria-hidden
        />
        <div className="relative flex flex-wrap items-center gap-4">
          <Avatar avatarKey={user?.profile.avatar_key} username={user?.username} size={56} />
          <div className="min-w-0">
            <p className="font-display text-lg">{user?.profile.display_name || user?.username}</p>
            <p className="text-xs uppercase tracking-wide text-[var(--color-ink-subtle)]">
              {user?.is_platform_admin ? "Administrador do Circuito" : "Piloto de vanguarda"}
            </p>
          </div>
        </div>

        <div className="relative mt-4 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat icon={LayoutGrid} label="Decks" value={deckCount} tint="var(--color-accent)" />
          <Stat icon={Library} label="Cartas" value={cardsCount} tint="var(--color-info)" />
          <Stat icon={Heart} label="Favoritas" value={favCount} tint="var(--color-danger)" />
          <Stat icon={Users} label="Amigos" value={user?.friend_count ?? 0} tint="var(--color-violet)" />
        </div>

        <div className="relative mt-4 flex flex-wrap gap-2">
          {lastDeck ? (
            <Link to={`/app/decks/${lastDeck.uuid}`}>
              <Button variant="secondary" size="sm">
                <Play className="h-4 w-4" /> Continuar “{lastDeck.title}”
              </Button>
            </Link>
          ) : (
            <Button variant="secondary" size="sm" onClick={() => create.mutate()} loading={create.isPending}>
              <Plus className="h-4 w-4" /> Criar meu primeiro deck
            </Button>
          )}
          <Link to="/app/collection"><Button variant="ghost" size="sm"><Library className="h-4 w-4" /> Coleção</Button></Link>
          <Link to="/app/tournaments"><Button variant="ghost" size="sm"><Swords className="h-4 w-4" /> Arena</Button></Link>
        </div>
      </Panel>

      {/* Arcade menu */}
      <div>
        <h2 className="font-display mb-3 flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
          <Sparkles className="h-4 w-4" /> Menu
        </h2>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {MENU.map(({ to, icon: Icon, title, desc, tint }) => (
            <Link key={to} to={to}>
              <Panel className="group relative h-full overflow-hidden p-5 transition-transform hover:-translate-y-1">
                <div
                  className="pointer-events-none absolute inset-x-0 bottom-0 h-1"
                  style={{ background: tint }}
                  aria-hidden
                />
                <span
                  className="grid h-11 w-11 place-items-center rounded-[var(--radius-card)] border-2 border-[var(--color-border)]"
                  style={{ background: `${tint}22` }}
                >
                  <Icon className="h-6 w-6" style={{ color: tint }} />
                </span>
                <h3 className="font-display mt-3 text-lg">{title}</h3>
                <p className="mt-1 text-sm text-[var(--color-ink-muted)]">{desc}</p>
                <span className="mt-3 inline-flex items-center gap-1 text-sm font-medium" style={{ color: tint }}>
                  Abrir <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" />
                </span>
              </Panel>
            </Link>
          ))}
        </div>
      </div>

      {/* Community feed */}
      <div>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="font-display flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
            <Flame className="h-4 w-4 text-[var(--color-danger)]" /> Decks em alta
          </h2>
          <Link to="/app/decks" className="text-xs font-medium text-[var(--color-accent)]">ver todos</Link>
        </div>
        {feedQ.isLoading ? (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-24 w-full" />)}
          </div>
        ) : feed.length === 0 ? (
          <Panel className="p-6 text-center text-sm text-[var(--color-ink-subtle)]">
            Nenhum deck público ainda. Publique o seu e apareça aqui!
          </Panel>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {feed.map((d) => (
              <a key={d.uuid} href={`/d/${d.uuid}`} target="_blank" rel="noreferrer">
                <Panel className={cn(
                  "group flex h-full items-center gap-3 overflow-hidden p-3 transition-transform hover:-translate-y-0.5",
                )}>
                  <div className="relative h-16 w-12 shrink-0 overflow-hidden rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface-3)]">
                    {d.cover_image ? (
                      <img src={d.cover_image} alt="" className="h-full w-full object-cover" />
                    ) : (
                      <div className="grid h-full w-full place-items-center">
                        {d.nation_focus && <NationLogo nation={d.nation_focus} size={22} />}
                      </div>
                    )}
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="font-display truncate text-sm">{d.title}</p>
                    <p className="truncate text-xs text-[var(--color-ink-subtle)]">
                      {d.nation_focus ? nationLabel(d.nation_focus) : d.format_code} · {d.main_count} cartas
                    </p>
                    <div className="mt-1 flex items-center gap-2">
                      <Avatar avatarKey={d.owner.avatar_key} username={d.owner.username} size={16} />
                      <span className="truncate text-[11px] text-[var(--color-ink-muted)]">{d.owner.username}</span>
                      <span className="ml-auto text-[11px] text-[var(--color-danger)]">♥ {d.like_count}</span>
                    </div>
                  </div>
                </Panel>
              </a>
            ))}
          </div>
        )}
      </div>

      {/* Admin */}
      {user?.is_platform_admin && (
        <Panel className="border-[var(--color-violet)]/40 p-5">
          <div className="flex items-center gap-2">
            <Wrench className="h-5 w-5 text-[var(--color-violet)]" />
            <h3 className="font-display text-lg">Ferramentas do admin</h3>
          </div>
          <p className="mt-1 text-sm text-[var(--color-ink-muted)]">
            Banlists oficiais, sincronização de catálogo e auditoria.
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <Link to="/app/banlists"><Button variant="ghost" size="sm">Banlists</Button></Link>
          </div>
        </Panel>
      )}
    </div>
  );
}
