import { useState } from "react";
import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Crown, Lock, ListChecks, Play, Trophy, UserPlus, Swords } from "lucide-react";
import { tournamentsApi, type Match } from "@/api/tournaments";
import { decksApi } from "@/api/decks";
import { useAuth } from "@/hooks/useAuth";
import { Avatar } from "@/components/Avatar";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { BracketView } from "@/features/tournaments/BracketView";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

type Tab = "overview" | "bracket" | "standings";

export function TournamentDetailPage() {
  const { uuid = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [tab, setTab] = useState<Tab>("overview");

  const { data: t, isLoading } = useQuery({ queryKey: ["tournament", uuid], queryFn: () => tournamentsApi.detail(uuid) });
  const { data: parts } = useQuery({ queryKey: ["t-participants", uuid], queryFn: () => tournamentsApi.participants(uuid) });
  const { data: stages } = useQuery({
    queryKey: ["t-bracket", uuid], queryFn: () => tournamentsApi.bracket(uuid),
    enabled: tab === "bracket" && !!t && ["running", "finished"].includes(t.status),
    refetchInterval: t?.status === "running" ? 8000 : false,
  });
  const { data: standings } = useQuery({
    queryKey: ["t-standings", uuid], queryFn: () => tournamentsApi.standings(uuid), enabled: tab === "standings",
  });
  const { data: regs } = useQuery({
    queryKey: ["t-regs", uuid], queryFn: () => tournamentsApi.registrations(uuid), enabled: !!t?.is_organizer,
  });
  const { data: myDecks } = useQuery({ queryKey: ["my-decks"], queryFn: decksApi.myDecks, enabled: !!t?.my_registration });

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["tournament", uuid] });
    qc.invalidateQueries({ queryKey: ["t-participants", uuid] });
    qc.invalidateQueries({ queryKey: ["t-bracket", uuid] });
    qc.invalidateQueries({ queryKey: ["t-standings", uuid] });
    qc.invalidateQueries({ queryKey: ["t-regs", uuid] });
  };

  const act = useMutation({
    mutationFn: ({ verb, body }: { verb: string; body?: unknown }) => tournamentsApi.action(uuid, verb, body),
    onSuccess: refresh,
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });
  const matchMut = useMutation({
    mutationFn: (fn: () => Promise<Match>) => fn(),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["t-bracket", uuid] }),
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });
  const submitDeck = useMutation({
    mutationFn: (deck: string) => tournamentsApi.submitDeck(uuid, deck),
    onSuccess: (sub) => {
      refresh();
      toast[sub.is_valid ? "success" : "info"](
        sub.is_valid ? "Deck submetido e válido!" : "Deck submetido (com avisos de validação)",
      );
    },
    onError: (e) => toast.error("Erro ao submeter", apiErrorMessage(e)),
  });

  if (isLoading || !t) return <Skeleton className="h-64 w-full" />;

  const isOrg = t.is_organizer;
  const myReg = t.my_registration;

  return (
    <div className="space-y-5">
      {/* Header */}
      <Panel className="overflow-hidden">
        <div className="relative aspect-[16/5] bg-[var(--color-surface-2)]">
          {t.image && <img src={t.image} alt="" className="h-full w-full object-cover" />}
          <div className="absolute inset-0 bg-gradient-to-t from-black/70 to-transparent" />
          <div className="absolute bottom-3 left-4 right-4">
            <div className="flex items-center gap-2">
              <Badge tone={t.status === "running" ? "brand" : t.status === "finished" ? "neutral" : "success"}>{t.status}</Badge>
              <Badge tone="neutral">{t.format_code}</Badge>
              <Badge tone="neutral">{t.bracket_type.replace(/_/g, " ")}</Badge>
            </div>
            <h1 className="font-display mt-1 text-2xl text-white drop-shadow">{t.name}</h1>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-3 p-4">
          <span className="flex items-center gap-1.5 text-sm"><Avatar avatarKey={t.organizer.avatar_key} username={t.organizer.username} size={22} /> {t.organizer.username}</span>
          <span className="text-sm text-[var(--color-ink-muted)]">{t.participant_count}/{t.max_participants} jogadores · Bo{t.best_of}</span>
          {t.banlist_uuid && <Badge tone="official">Banlist v{t.banlist_version_number ?? "?"}</Badge>}
          {t.power_policy && <Badge tone="warning">Power: {t.power_policy.kind}</Badge>}

          {/* Player actions */}
          <div className="ml-auto flex flex-wrap gap-2">
            {!isOrg && t.status === "registration" && !myReg && (
              <Button loading={act.isPending} onClick={() => act.mutate({ verb: "register" })}>
                <UserPlus className="h-4 w-4" /> Inscrever-se
              </Button>
            )}
            {myReg && <Badge tone="success">Inscrito ({myReg.status})</Badge>}
            {myReg && t.status === "check_in" && (
              <Button onClick={() => act.mutate({ verb: "check-in" })}><Check className="h-4 w-4" /> Check-in</Button>
            )}
          </div>
        </div>
      </Panel>

      {/* Organizer control bar */}
      {isOrg && (
        <Panel className="flex flex-wrap items-center gap-2 p-3">
          <span className="font-display text-[10px] uppercase text-[var(--color-violet)]">Organizador</span>
          {t.status === "draft" && <Button size="sm" onClick={() => act.mutate({ verb: "open-registration" })}><Play className="h-4 w-4" /> Abrir inscrições</Button>}
          {["registration"].includes(t.status) && <Button size="sm" onClick={() => act.mutate({ verb: "lock" })}><Lock className="h-4 w-4" /> Travar inscrições</Button>}
          {["locked", "check_in"].includes(t.status) && (
            <Button size="sm" onClick={() => act.mutate({ verb: "generate-bracket" })}><Swords className="h-4 w-4" /> Gerar bracket</Button>
          )}
          {t.invite_code && <Badge tone="neutral">convite: {t.invite_code}</Badge>}
        </Panel>
      )}

      {/* Deck submission */}
      {myReg && t.requires_decklist && ["registration", "check_in", "locked"].includes(t.status) && (
        <Panel className="p-4">
          <h3 className="font-display mb-2 text-sm uppercase text-[var(--color-ink-muted)]">Submeter deck</h3>
          <div className="flex flex-wrap gap-2">
            {(myDecks?.results ?? []).filter((d) => d.format_code === t.format_code).map((d) => (
              <Button key={d.uuid} size="sm" variant="secondary" loading={submitDeck.isPending}
                onClick={() => submitDeck.mutate(d.uuid)}>{d.title}</Button>
            ))}
            {(myDecks?.results ?? []).filter((d) => d.format_code === t.format_code).length === 0 && (
              <p className="text-sm text-[var(--color-ink-subtle)]">Crie um deck no formato {t.format_code} para submeter.</p>
            )}
          </div>
        </Panel>
      )}

      {/* Tabs */}
      <div className="flex gap-1">
        {([["overview", "Visão geral", ListChecks], ["bracket", "Bracket", Swords], ["standings", "Standings", Trophy]] as const).map(([key, label, Icon]) => (
          <button key={key} onClick={() => setTab(key)}
            className={cn("font-display flex items-center gap-2 rounded-[var(--radius-card)] border-2 px-4 py-2 text-xs uppercase",
              tab === key ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]" : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]")}>
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      {tab === "overview" && (
        <div className="grid gap-4 lg:grid-cols-2">
          <Panel className="p-4">
            <h3 className="font-display mb-2 text-sm uppercase text-[var(--color-ink-muted)]">Participantes ({parts?.length ?? 0})</h3>
            <ul className="space-y-1.5">
              {(parts ?? []).map((p) => (
                <li key={p.uuid} className="flex items-center gap-2 text-sm">
                  <span className="font-display w-5 text-[10px] text-[var(--color-ink-subtle)]">{p.seed ?? "–"}</span>
                  <Avatar avatarKey={p.user.avatar_key} username={p.user.username} size={24} />
                  <span className="flex-1">{p.user.username}</span>
                  {p.checked_in && <Badge tone="success">check-in</Badge>}
                  {p.has_submission && <Badge tone="brand">deck</Badge>}
                  {p.status === "disqualified" && <Badge tone="danger">DQ</Badge>}
                  {isOrg && p.status !== "disqualified" && (
                    <button onClick={() => act.mutate({ verb: "disqualify", body: { participant: p.uuid } })}
                      className="text-[10px] text-[var(--color-danger)] hover:underline">DQ</button>
                  )}
                </li>
              ))}
            </ul>
          </Panel>
          <Panel className="p-4">
            {t.description && <p className="mb-3 whitespace-pre-line text-sm text-[var(--color-ink-muted)]">{t.description}</p>}
            {t.prizes && <><h4 className="font-display text-xs uppercase text-[var(--color-ink-subtle)]">Premiação</h4><p className="mb-2 text-sm">{t.prizes}</p></>}
            {isOrg && (regs?.filter((r) => r.status === "pending").length ?? 0) > 0 && (
              <div className="mt-3">
                <h4 className="font-display mb-1 text-xs uppercase text-[var(--color-ink-subtle)]">Inscrições pendentes</h4>
                {regs!.filter((r) => r.status === "pending").map((r) => (
                  <div key={r.uuid} className="flex items-center gap-2 py-1 text-sm">
                    <span className="flex-1">{r.user.username}</span>
                    <Button size="sm" onClick={() => act.mutate({ verb: "review-registration", body: { registration: r.uuid, status: "approved" } })}>Aprovar</Button>
                    <Button size="sm" variant="ghost" onClick={() => act.mutate({ verb: "review-registration", body: { registration: r.uuid, status: "rejected" } })}>Recusar</Button>
                  </div>
                ))}
              </div>
            )}
          </Panel>
        </div>
      )}

      {tab === "bracket" && (
        <Panel className="p-4">
          {stages && stages.length > 0 ? (
            <BracketView
              stages={stages}
              currentUserId={user?.uuid}
              isOrganizer={isOrg}
              onReport={(m, a, b) => matchMut.mutate(() => tournamentsApi.reportMatch(m.uuid, a, b))}
              onConfirm={(m) => matchMut.mutate(() => tournamentsApi.confirmMatch(m.uuid))}
              onSetResult={(m, a, b) => matchMut.mutate(() => tournamentsApi.setResult(m.uuid, a, b))}
            />
          ) : (
            <p className="text-sm text-[var(--color-ink-subtle)]">Bracket ainda não gerado.</p>
          )}
        </Panel>
      )}

      {tab === "standings" && (
        <Panel className="p-4">
          {(standings?.length ?? 0) === 0 ? (
            <p className="text-sm text-[var(--color-ink-subtle)]">Sem standings ainda.</p>
          ) : (
            <ul className="space-y-1">
              {standings!.map((s) => (
                <li key={s.participant.uuid} className="flex items-center gap-3 rounded-[6px] bg-[var(--color-surface-2)] px-3 py-2 text-sm">
                  <span className={cn("font-display w-7 text-center", s.rank === 1 && "text-[var(--color-accent)]")}>
                    {s.rank === 1 ? <Crown className="mx-auto h-4 w-4" /> : s.rank}
                  </span>
                  <Avatar avatarKey={s.participant.user.avatar_key} username={s.participant.user.username} size={24} />
                  <span className="flex-1">{s.participant.user.username}</span>
                  {s.tiebreaks?.omw != null && (
                    <span className="font-display text-[10px] text-[var(--color-ink-subtle)]" title="Opponents' Match-Win %">
                      OMW {Math.round(s.tiebreaks.omw * 100)}%
                    </span>
                  )}
                  <span className="font-display text-xs text-[var(--color-ink-muted)]">{s.wins}V {s.losses}D{s.draws ? ` ${s.draws}E` : ""}</span>
                  <span className="font-display text-sm">{s.points} pts</span>
                </li>
              ))}
            </ul>
          )}
        </Panel>
      )}
    </div>
  );
}
