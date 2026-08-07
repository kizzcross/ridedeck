import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, ArrowLeft, Crown, Dices, Gavel, RefreshCw, ShieldAlert } from "lucide-react";
import { tournamentsApi, type Roster } from "@/api/tournaments";
import { Avatar } from "@/components/Avatar";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { PowerBadge } from "@/features/championship/PowerBadge";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

const PENALTY_KINDS = [
  { v: "warning", label: "Advertência", points: 0 },
  { v: "points_deduction", label: "Perda de pontos", points: -3 },
  { v: "game_loss", label: "Derrota na partida", points: 0 },
  { v: "match_loss", label: "Derrota no confronto", points: 0 },
  { v: "disqualification", label: "Desclassificação", points: 0 },
];

export function OwnerControlPanelPage() {
  const { uuid = "" } = useParams();
  const toast = useToast();
  const qc = useQueryClient();

  const { data: t } = useQuery({ queryKey: ["tournament", uuid], queryFn: () => tournamentsApi.detail(uuid) });
  const { data: rosters, isLoading } = useQuery({
    queryKey: ["t-rosters", uuid], queryFn: () => tournamentsApi.rosters(uuid), enabled: !!t?.is_organizer,
  });
  const { data: penalties } = useQuery({ queryKey: ["t-penalties", uuid], queryFn: () => tournamentsApi.penalties(uuid), enabled: !!t?.is_organizer });
  const { data: rounds } = useQuery({ queryKey: ["roster-rounds", uuid], queryFn: () => tournamentsApi.rosterRounds(uuid), enabled: !!t?.is_organizer, refetchInterval: 8000 });
  const disputed = (rounds ?? []).flatMap((r) => r.matches).filter((m) => m.state === "disputed");

  const refresh = () => {
    qc.invalidateQueries({ queryKey: ["t-rosters", uuid] });
    qc.invalidateQueries({ queryKey: ["t-penalties", uuid] });
    qc.invalidateQueries({ queryKey: ["roster-rounds", uuid] });
  };
  const onErr = (e: unknown) => toast.error("Erro", apiErrorMessage(e));

  const setPower = useMutation({
    mutationFn: (v: { rd: string; power: number }) => tournamentsApi.setDeckPower(uuid, v.rd, v.power),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["t-rosters", uuid] }),
    onError: onErr,
  });
  const penalize = useMutation({
    mutationFn: (v: { participant: string; kind: string; points: number; reason: string }) => tournamentsApi.applyPenalty(uuid, v),
    onSuccess: () => { refresh(); toast.success("Penalidade aplicada."); },
    onError: onErr,
  });
  const runDraws = useMutation({ mutationFn: (redraw: boolean) => tournamentsApi.runDraws(uuid, redraw), onSuccess: () => toast.success("Sorteios atualizados."), onError: onErr });
  const resolveDispute = useMutation({
    mutationFn: (v: { m: string; a?: number; b?: number }) => tournamentsApi.resolveDispute(v.m, "Resolvido pelo organizador.", v.a, v.b),
    onSuccess: () => { refresh(); toast.success("Disputa resolvida."); }, onError: onErr,
  });

  if (!t) return <Skeleton className="h-[70vh] w-full" />;
  if (!t.is_organizer) {
    return <Panel className="p-8 text-center text-sm text-[var(--color-ink-muted)]">Apenas o organizador acessa este painel.</Panel>;
  }

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Link to={`/app/tournaments/${uuid}`}><Button size="sm" variant="ghost"><ArrowLeft className="h-4 w-4" /></Button></Link>
        <div className="min-w-0 flex-1">
          <h1 className="font-display truncate text-2xl"><span className="text-gradient">Painel do organizador</span></h1>
          <p className="truncate text-sm text-[var(--color-ink-muted)]">{t.name}</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="secondary" loading={runDraws.isPending} onClick={() => runDraws.mutate(false)}><Dices className="h-4 w-4" /> Sortear rodada</Button>
          <Button size="sm" variant="ghost" loading={runDraws.isPending} onClick={() => runDraws.mutate(true)} title="Re-sortear (registrado)"><RefreshCw className="h-4 w-4" /></Button>
        </div>
      </div>

      {/* Power editing across all rosters */}
      <section>
        <h2 className="font-display mb-2 flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
          <Crown className="h-4 w-4 text-[var(--color-accent)]" /> Notas de força dos decks
        </h2>
        <p className="mb-3 text-[13px] text-[var(--color-ink-muted)]">
          Ajuste a força de cada deck aqui. O limite deste campeonato é <strong className="text-[var(--color-ink)]">{t.power_cap}</strong>.
          Times acima do limite ficam destacados em vermelho.
        </p>
        {isLoading ? <Skeleton className="h-40 w-full" /> : (
          <div className="space-y-2">
            {(rosters ?? []).map((r) => (
              <RosterRow key={r.uuid} r={r} cap={t.power_cap}
                onSetPower={(rd, power) => setPower.mutate({ rd, power })}
                onPenalize={(participant, kind, points, reason) => penalize.mutate({ participant, kind, points, reason })}
              />
            ))}
            {(rosters ?? []).length === 0 && <Panel className="p-6 text-center text-sm text-[var(--color-ink-subtle)]">Nenhum jogador inscrito ainda.</Panel>}
          </div>
        )}
      </section>

      {/* Disputes */}
      {disputed.length > 0 && (
        <section>
          <h2 className="font-display mb-2 flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
            <Gavel className="h-4 w-4 text-[var(--color-warning)]" /> Resultados contestados
          </h2>
          <div className="space-y-2">
            {disputed.map((m) => (
              <Panel key={m.uuid} className="flex flex-wrap items-center gap-3 border-[var(--color-warning)]/50 p-3 text-sm">
                <span className="flex-1">
                  {m.participant_a?.user.username} <span className="text-[var(--color-ink-subtle)]">vs</span> {m.participant_b?.user.username}
                  <span className="ml-2 text-[var(--color-ink-subtle)]">({m.score_a}–{m.score_b} reportado)</span>
                </span>
                <Button size="sm" variant="secondary" loading={resolveDispute.isPending}
                  onClick={() => resolveDispute.mutate({ m: m.uuid, a: 1, b: 0 })}>
                  Vitória {m.participant_a?.user.username}
                </Button>
                <Button size="sm" variant="secondary" loading={resolveDispute.isPending}
                  onClick={() => resolveDispute.mutate({ m: m.uuid, a: 0, b: 1 })}>
                  Vitória {m.participant_b?.user.username}
                </Button>
                <Button size="sm" variant="ghost" loading={resolveDispute.isPending}
                  onClick={() => resolveDispute.mutate({ m: m.uuid })}>
                  Manter reportado
                </Button>
              </Panel>
            ))}
          </div>
        </section>
      )}

      {/* Penalties log */}
      {(penalties?.length ?? 0) > 0 && (
        <section>
          <h2 className="font-display mb-2 flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
            <ShieldAlert className="h-4 w-4 text-[var(--color-danger)]" /> Penalidades aplicadas
          </h2>
          <Panel className="divide-y divide-[var(--color-border)] p-0">
            {penalties!.map((p) => (
              <div key={p.uuid} className="flex items-center gap-3 px-3 py-2 text-sm">
                <span className="flex-1">{p.participant}</span>
                <Badge tone="danger">{p.kind}{p.points ? ` ${p.points}` : ""}</Badge>
                <span className="text-[var(--color-ink-subtle)]">{p.reason}</span>
              </div>
            ))}
          </Panel>
        </section>
      )}
    </div>
  );
}

function RosterRow({
  r, cap, onSetPower, onPenalize,
}: {
  r: Roster; cap: number;
  onSetPower: (rosterDeckUuid: string, power: number) => void;
  onPenalize: (participant: string, kind: string, points: number, reason: string) => void;
}) {
  const [penOpen, setPenOpen] = useState(false);
  return (
    <Panel className={cn("p-3", r.is_over_cap && "border-[var(--color-danger)]")}>
      <div className="flex items-center gap-3">
        <Avatar avatarKey={r.participant.user.avatar_key} username={r.participant.user.username} size={26} />
        <span className="flex-1 truncate font-display text-sm">{r.participant.user.username}</span>
        <span className={cn("font-display text-sm", r.is_over_cap ? "text-[var(--color-danger)]" : "text-[var(--color-ink-muted)]")}>
          {r.power_used}/{cap}
        </span>
        {r.is_over_cap && (
          <span className="flex items-center gap-1 text-[11px] text-[var(--color-danger)]"><AlertTriangle className="h-3.5 w-3.5" /> acima</span>
        )}
        <button onClick={() => setPenOpen((o) => !o)} className="text-[var(--color-ink-subtle)] hover:text-[var(--color-danger)]" title="Aplicar penalidade">
          <Gavel className="h-4 w-4" />
        </button>
      </div>

      {/* Inline per-deck power editing */}
      <div className="mt-2 flex flex-wrap gap-2 border-t border-[var(--color-border)] pt-2">
        {r.decks.map((d) => (
          <div key={d.uuid} className="flex items-center gap-1.5 rounded-[6px] bg-[var(--color-surface-2)] px-2 py-1">
            {d.is_ace && <Crown className="h-3 w-3 text-[var(--color-accent)]" />}
            <span className="max-w-[8rem] truncate text-[11px]">{d.label}</span>
            <input
              type="number" min={0} defaultValue={d.power ?? undefined}
              disabled={d.locked}
              onBlur={(e) => { const v = e.target.value; if (v !== "" && +v !== d.power) onSetPower(d.uuid, +v); }}
              className="h-6 w-12 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-1 text-center text-xs"
              aria-label={`Força de ${d.label}`}
            />
            {d.power == null && <PowerBadge power={null} size="sm" />}
          </div>
        ))}
      </div>

      {penOpen && <PenaltyForm onApply={(kind, points, reason) => { onPenalize(r.participant.uuid, kind, points, reason); setPenOpen(false); }} />}
    </Panel>
  );
}

function PenaltyForm({ onApply }: { onApply: (kind: string, points: number, reason: string) => void }) {
  const [kind, setKind] = useState("warning");
  const [points, setPoints] = useState(0);
  const [reason, setReason] = useState("");
  return (
    <div className="mt-2 flex flex-wrap items-end gap-2 border-t border-[var(--color-border)] pt-2">
      <label className="text-xs">
        <span className="font-display mb-0.5 block text-[9px] uppercase text-[var(--color-ink-muted)]">Tipo</span>
        <select value={kind} onChange={(e) => { setKind(e.target.value); setPoints(PENALTY_KINDS.find((k) => k.v === e.target.value)?.points ?? 0); }}
          className="h-8 rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs">
          {PENALTY_KINDS.map((k) => <option key={k.v} value={k.v}>{k.label}</option>)}
        </select>
      </label>
      <label className="text-xs">
        <span className="font-display mb-0.5 block text-[9px] uppercase text-[var(--color-ink-muted)]">Pontos</span>
        <input type="number" value={points} onChange={(e) => setPoints(+e.target.value)} className="h-8 w-16 rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs" />
      </label>
      <label className="min-w-[8rem] flex-1 text-xs">
        <span className="font-display mb-0.5 block text-[9px] uppercase text-[var(--color-ink-muted)]">Motivo</span>
        <input value={reason} onChange={(e) => setReason(e.target.value)} placeholder="Motivo…" className="h-8 w-full rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-2 text-xs" />
      </label>
      <Button size="sm" variant="danger" onClick={() => onApply(kind, points, reason)}>Aplicar</Button>
    </div>
  );
}
