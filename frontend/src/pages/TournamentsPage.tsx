import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Crown, Plus, Swords, Users, Wifi, MapPin } from "lucide-react";
import { tournamentsApi, type TournamentListItem } from "@/api/tournaments";
import { Avatar } from "@/components/Avatar";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

const STATUS_TONE: Record<string, "success" | "warning" | "neutral" | "brand"> = {
  registration: "success",
  running: "brand",
  check_in: "warning",
  locked: "warning",
  finished: "neutral",
  draft: "neutral",
  cancelled: "neutral",
};
const STATUS_LABEL: Record<string, string> = {
  draft: "Rascunho", registration: "Inscrições abertas", locked: "Travado",
  check_in: "Check-in", running: "Em andamento", finished: "Encerrado", cancelled: "Cancelado",
};

function TournamentCard({ t }: { t: TournamentListItem }) {
  return (
    <Link to={`/app/tournaments/${t.uuid}`}>
      <Panel className="rd-card h-full overflow-hidden">
        <div className="relative aspect-[16/6] bg-[var(--color-surface-2)]">
          {t.image ? <img src={t.image} alt="" className="h-full w-full object-cover" /> : (
            <div className="grid h-full place-items-center"><Swords className="h-8 w-8 text-[var(--color-ink-subtle)]" /></div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
          <Badge tone={STATUS_TONE[t.status]} className="absolute right-2 top-2">{STATUS_LABEL[t.status]}</Badge>
          {t.kind === "roster" && (
            <Badge tone="accent" className="absolute left-2 top-2"><Crown className="h-3 w-3" /> Campeonato</Badge>
          )}
        </div>
        <div className="p-3">
          <h3 className="font-display line-clamp-1 text-sm">{t.name}</h3>
          <p className="font-display mt-0.5 text-[10px] uppercase text-[var(--color-ink-subtle)]">
            {t.kind === "roster" ? `${t.format_code} · time de decks` : `${t.format_code} · ${t.bracket_type.replace(/_/g, " ")}`}
          </p>
          <div className="mt-2 flex items-center gap-3 text-[11px] text-[var(--color-ink-muted)]">
            <span className="flex items-center gap-1"><Users className="h-3 w-3" /> {t.participant_count}/{t.max_participants}</span>
            <span className="flex items-center gap-1">{t.is_online ? <Wifi className="h-3 w-3" /> : <MapPin className="h-3 w-3" />} {t.is_online ? "Online" : "Presencial"}</span>
            <span className="ml-auto flex items-center gap-1"><Avatar avatarKey={t.organizer.avatar_key} username={t.organizer.username} size={16} /> {t.organizer.username}</span>
          </div>
        </div>
      </Panel>
    </Link>
  );
}

export function TournamentsPage() {
  const navigate = useNavigate();
  const toast = useToast();
  const qc = useQueryClient();
  const [creating, setCreating] = useState(false);
  const [name, setName] = useState("");
  const [bracket, setBracket] = useState("single_elimination");

  const { data, isLoading } = useQuery({ queryKey: ["tournaments"], queryFn: () => tournamentsApi.list() });

  const create = useMutation({
    mutationFn: () => tournamentsApi.create({ name: name || "Novo torneio", bracket_type: bracket }),
    onSuccess: (t) => { qc.invalidateQueries({ queryKey: ["tournaments"] }); navigate(`/app/tournaments/${t.uuid}`); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <h1 className="font-display flex items-center gap-2 text-2xl">
          <Swords className="h-6 w-6 text-[var(--color-accent)]" />
          <span className="text-gradient">Torneios</span>
        </h1>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={() => setCreating((s) => !s)}><Plus className="h-4 w-4" /> Torneio rápido</Button>
          <Button onClick={() => navigate("/app/tournaments/new")}><Crown className="h-4 w-4" /> Novo campeonato</Button>
        </div>
      </div>

      {creating && (
        <Panel className="rd-fade-in flex flex-wrap items-end gap-3 p-4">
          <label className="flex-1">
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Nome</span>
            <input value={name} onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && create.mutate()} autoFocus
              placeholder="Copa de Verão…"
              className="h-10 w-full rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm" />
          </label>
          <label>
            <span className="font-display mb-1 block text-[10px] uppercase text-[var(--color-ink-muted)]">Formato do bracket</span>
            <select value={bracket} onChange={(e) => setBracket(e.target.value)}
              className="h-10 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm">
              <option value="single_elimination">Single elimination</option>
              <option value="swiss">Swiss</option>
              <option value="swiss_top_cut">Swiss + Top Cut</option>
              <option value="double_elimination">Double elimination</option>
              <option value="round_robin">Round robin</option>
            </select>
          </label>
          <Button loading={create.isPending} onClick={() => create.mutate()}>Criar e configurar</Button>
          <p className="w-full text-xs text-[var(--color-ink-subtle)]">
            Para o modo <strong>campeonato de decks</strong> (roster, cap de força, sorteio, Ace), use o botão <strong>Novo campeonato</strong>.
          </p>
        </Panel>
      )}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-48" />)}
        </div>
      ) : (data?.results.length ?? 0) === 0 ? (
        <Panel className="p-10 text-center text-sm text-[var(--color-ink-muted)]">Nenhum torneio ainda. Crie o primeiro!</Panel>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {data!.results.map((t) => <TournamentCard key={t.uuid} t={t} />)}
        </div>
      )}
    </div>
  );
}
