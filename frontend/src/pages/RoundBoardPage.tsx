import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Dices, RefreshCw } from "lucide-react";
import { tournamentsApi, type Roster, type RosterRound, type SelectionDeck } from "@/api/tournaments";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { VersusBoard } from "@/features/championship/VersusBoard";
import { DrawAnimator } from "@/features/championship/DrawAnimator";
import { ExplainerCallout } from "@/features/championship/Explainer";
import { SELECTION_MODE_HELP } from "@/features/championship/copy";
import { apiErrorMessage } from "@/lib/api";

const MANUAL_MODES = new Set(["manual", "choose_from_random"]);

export function RoundBoardPage() {
  const { uuid = "" } = useParams();
  const toast = useToast();
  const qc = useQueryClient();

  const { data: t } = useQuery({ queryKey: ["tournament", uuid], queryFn: () => tournamentsApi.detail(uuid) });
  const { data: rounds, isLoading } = useQuery({
    queryKey: ["roster-rounds", uuid],
    queryFn: () => tournamentsApi.rosterRounds(uuid),
    refetchInterval: t?.status === "running" ? 5000 : false,
  });
  const { data: rosterData } = useQuery({ queryKey: ["my-roster", uuid], queryFn: () => tournamentsApi.myRoster(uuid) });
  const myRoster = (rosterData && "uuid" in rosterData ? rosterData : null) as Roster | null;
  const meParticipantUuid = myRoster?.participant.uuid ?? null;

  const invalidate = () => qc.invalidateQueries({ queryKey: ["roster-rounds", uuid] });
  const onErr = (e: unknown) => toast.error("Erro", apiErrorMessage(e));

  const runDraws = useMutation({ mutationFn: (redraw: boolean) => tournamentsApi.runDraws(uuid, redraw), onSuccess: invalidate, onError: onErr });
  const pick = useMutation({ mutationFn: (v: { m: string; d: string }) => tournamentsApi.pickDeck(v.m, v.d), onSuccess: invalidate, onError: onErr });
  const ready = useMutation({ mutationFn: (m: string) => tournamentsApi.confirmSelection(m), onSuccess: invalidate, onError: onErr });
  const report = useMutation({ mutationFn: (v: { m: string; a: number; b: number }) => tournamentsApi.reportMatch(v.m, v.a, v.b), onSuccess: invalidate, onError: onErr });
  const confirmRes = useMutation({ mutationFn: (m: string) => tournamentsApi.confirmMatch(m), onSuccess: invalidate, onError: onErr });
  const useAce = useMutation({ mutationFn: (m: string) => tournamentsApi.useAce(m), onSuccess: () => { invalidate(); toast.success("Ace ativado nesta partida!"); }, onError: onErr });
  const dispute = useMutation({ mutationFn: (m: string) => tournamentsApi.disputeMatch(m, "Resultado contestado pelo jogador."), onSuccess: () => { invalidate(); toast.info("Organizador chamado", "A partida foi marcada como contestada."); }, onError: onErr });

  const activeRound: RosterRound | undefined = useMemo(() => {
    if (!rounds?.length) return undefined;
    return [...rounds].reverse().find((r) => r.status === "active") ?? rounds[rounds.length - 1];
  }, [rounds]);

  // Auto-play the "sorteio" animation once per newly drawn deck (random modes).
  const animated = useRef<Set<string>>(new Set());
  const [draw, setDraw] = useState<{ deck: SelectionDeck; pool: number } | null>(null);
  useEffect(() => {
    if (!activeRound || !meParticipantUuid) return;
    for (const m of activeRound.matches) {
      const sel = m.selections.find((s) => s.participant_uuid === meParticipantUuid);
      if (sel?.deck && !sel.confirmed && ["random", "predetermined"].includes(sel.method) && !animated.current.has(m.uuid)) {
        animated.current.add(m.uuid);
        setDraw({ deck: sel.deck, pool: myRoster?.decks.length ?? 4 });
        break;
      }
    }
  }, [activeRound, meParticipantUuid, myRoster]);

  const busy = pick.isPending || ready.isPending || report.isPending || confirmRes.isPending;

  if (isLoading || !t) return <Skeleton className="h-[70vh] w-full" />;

  const isOrg = t.is_organizer;
  const manual = MANUAL_MODES.has(t.deck_selection_mode);
  const aceSpendable = t.ace_enabled && ["manual_once", "replace_draw"].includes(t.ace_rule);

  const reportFor = (m: { uuid: string }, side: "a" | "b", win: boolean) => {
    const iWin = win;
    const aWins = side === "a" ? iWin : !iWin;
    report.mutate({ m: m.uuid, a: aWins ? 1 : 0, b: aWins ? 0 : 1 });
  };

  return (
    <div className="space-y-5">
      <div className="flex flex-wrap items-center gap-3">
        <Link to={`/app/tournaments/${uuid}`}><Button size="sm" variant="ghost"><ArrowLeft className="h-4 w-4" /></Button></Link>
        <div className="min-w-0 flex-1">
          <h1 className="font-display truncate text-2xl"><span className="text-gradient">Rodada</span></h1>
          <p className="truncate text-sm text-[var(--color-ink-muted)]">{t.name}</p>
        </div>
        {activeRound && <Badge tone="brand">{activeRound.name || `Rodada ${activeRound.number}`}</Badge>}
        {isOrg && activeRound && (
          <div className="flex gap-2">
            <Button size="sm" variant="secondary" loading={runDraws.isPending} onClick={() => runDraws.mutate(false)}>
              <Dices className="h-4 w-4" /> Sortear
            </Button>
            <Button size="sm" variant="ghost" loading={runDraws.isPending} onClick={() => runDraws.mutate(true)} title="Re-sortear (intervenção registrada)">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        )}
      </div>

      <ExplainerCallout id="round-help" title="O que acontece nesta tela">
        <p>
          Aqui você joga a partida da rodada usando um dos decks do seu time.
          {" "}{SELECTION_MODE_HELP[t.deck_selection_mode]}
        </p>
        <p>
          O deck do adversário fica <strong className="text-[var(--color-ink)]">virado para baixo</strong> até os dois
          confirmarem que estão prontos — aí os dois aparecem ao mesmo tempo. Depois de jogar, diga se você venceu; o
          adversário confirma o resultado.
        </p>
      </ExplainerCallout>

      {!activeRound || activeRound.matches.length === 0 ? (
        <Panel className="p-10 text-center text-sm text-[var(--color-ink-subtle)]">
          Nenhuma rodada ativa. {isOrg ? "Gere o bracket no campeonato." : "Aguarde o organizador iniciar."}
        </Panel>
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {activeRound.matches.map((m) => {
            const mine = m.participant_a?.uuid === meParticipantUuid || m.participant_b?.uuid === meParticipantUuid;
            const side: "a" | "b" | null = m.participant_a?.uuid === meParticipantUuid ? "a"
              : m.participant_b?.uuid === meParticipantUuid ? "b" : null;
            return (
              <VersusBoard
                key={m.uuid}
                match={m}
                meParticipantUuid={meParticipantUuid}
                myRosterDecks={myRoster?.decks}
                manualMode={manual}
                busy={busy && mine}
                onPick={(d) => pick.mutate({ m: m.uuid, d })}
                onConfirmReady={() => ready.mutate(m.uuid)}
                onReport={(win) => side && reportFor(m, side, win)}
                onConfirmResult={() => confirmRes.mutate(m.uuid)}
                canUseAce={aceSpendable && mine}
                onUseAce={() => useAce.mutate(m.uuid)}
                onDispute={() => dispute.mutate(m.uuid)}
              />
            );
          })}
        </div>
      )}

      <DrawAnimator
        open={!!draw}
        deckLabel={draw?.deck.label ?? ""}
        deckCover={draw?.deck.cover_image}
        isAce={draw?.deck.is_ace}
        poolSize={draw?.pool}
        onClose={() => setDraw(null)}
      />
    </div>
  );
}
