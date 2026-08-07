import { motion } from "framer-motion";
import { Crown, Flag, Swords } from "lucide-react";
import type { RosterDeck, RosterMatch, RosterMatchSelection } from "@/api/tournaments";
import { Avatar } from "@/components/Avatar";
import { Button } from "@/components/ui";
import { useReduceMotion } from "@/app/MotionProvider";
import { AceSeal } from "./AceSeal";
import { cn } from "@/lib/cn";

type Side = "a" | "b";

/** A single roster-championship match presented as a versus board. The opponent's
 *  deck stays face-down until both players confirm (the server gates the reveal);
 *  when it flips, a short flourish plays (suppressed under reduced motion). */
export function VersusBoard({
  match,
  meParticipantUuid,
  myRosterDecks,
  manualMode,
  onPick,
  onConfirmReady,
  onReport,
  onConfirmResult,
  onUseAce,
  onDispute,
  canUseAce,
  busy,
}: {
  match: RosterMatch;
  meParticipantUuid?: string | null;
  myRosterDecks?: RosterDeck[];
  manualMode?: boolean;
  onPick?: (rosterDeckUuid: string) => void;
  onConfirmReady?: () => void;
  onReport?: (win: boolean) => void;
  onConfirmResult?: () => void;
  onUseAce?: () => void;
  onDispute?: () => void;
  canUseAce?: boolean;
  busy?: boolean;
}) {
  const reduce = useReduceMotion();
  const selOf = (pid?: string): RosterMatchSelection | undefined =>
    match.selections.find((s) => s.participant_uuid === pid);
  const selA = selOf(match.participant_a?.uuid);
  const selB = selOf(match.participant_b?.uuid);
  const mySide: Side | null =
    match.participant_a?.uuid === meParticipantUuid ? "a"
      : match.participant_b?.uuid === meParticipantUuid ? "b" : null;
  const mySel = mySide === "a" ? selA : selB;
  const bothRevealed = !!selA?.deck && !!selB?.deck;
  const done = match.state === "done";

  return (
    <div className="overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)]">
      <div className="flex flex-col items-stretch sm:grid sm:grid-cols-[1fr_auto_1fr]">
        <PlayerSide side="a" match={match} sel={selA} reduce={reduce} win={done && match.winner_uuid === match.participant_a?.uuid} />
        <div className="flex flex-row items-center justify-center gap-2 bg-[var(--color-surface-3)] px-3 py-2 sm:flex-col sm:py-0">
          <motion.div
            initial={false}
            animate={bothRevealed && !reduce ? { scale: [1, 1.25, 1] } : {}}
            transition={{ duration: 0.5 }}
            className="font-display grid h-9 w-9 place-items-center rounded-full border-2 border-[var(--color-accent)] text-[var(--color-accent)]"
          >
            <Swords className="h-5 w-5" />
          </motion.div>
          <span className="font-display text-[9px] uppercase tracking-widest text-[var(--color-ink-subtle)]">VS</span>
        </div>
        <PlayerSide side="b" match={match} sel={selB} reduce={reduce} mirror win={done && match.winner_uuid === match.participant_b?.uuid} />
      </div>

      {/* Actions for the current player */}
      {mySide && !done && (
        <div className="border-t-2 border-[var(--color-border)] p-3">
          {/* Manual / choose: pick a deck first */}
          {manualMode && !mySel?.confirmed && (
            <PickRow
              options={mySel?.options?.length ? mySel.options : undefined}
              myDecks={myRosterDecks}
              current={mySel?.deck?.uuid}
              onPick={onPick}
              busy={busy}
            />
          )}
          {!bothRevealed && !mySel?.confirmed && mySel?.deck && (
            <div className="space-y-1.5">
              {canUseAce && !mySel.is_ace_used && (
                <Button variant="secondary" className="w-full" loading={busy} onClick={onUseAce}>
                  <Crown className="h-4 w-4" /> Usar meu Ace nesta partida
                </Button>
              )}
              <Button className="w-full" loading={busy} onClick={onConfirmReady}>
                {mySel.is_ace_used ? "Confirmar (com Ace)" : "Estou pronto"}
              </Button>
            </div>
          )}
          {mySel?.confirmed && !bothRevealed && (
            <p className="text-center text-xs text-[var(--color-ink-muted)]">
              Você está pronto — aguardando o oponente confirmar…
            </p>
          )}
          {bothRevealed && match.state === "reported" && (
            <div className="space-y-1.5">
              <p className="text-center text-xs text-[var(--color-ink-muted)]">
                Resultado reportado — confirme se estiver correto.
              </p>
              <div className="flex gap-2">
                <Button className="flex-1" loading={busy} onClick={onConfirmResult}>Confirmar resultado</Button>
                {onDispute && (
                  <Button variant="ghost" loading={busy} onClick={onDispute} title="Contestar / chamar o organizador">
                    <Flag className="h-4 w-4" /> Contestar
                  </Button>
                )}
              </div>
            </div>
          )}
          {bothRevealed && match.state === "pending" && (
            <div className="flex gap-2">
              <Button className="flex-1" loading={busy} onClick={() => onReport?.(true)}>Venci</Button>
              <Button className="flex-1" variant="secondary" loading={busy} onClick={() => onReport?.(false)}>Perdi</Button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

function PlayerSide({
  side, match, sel, reduce, mirror, win,
}: {
  side: Side; match: RosterMatch; sel?: RosterMatchSelection; reduce: boolean; mirror?: boolean; win?: boolean;
}) {
  const p = side === "a" ? match.participant_a : match.participant_b;
  return (
    <div className={cn("flex flex-col gap-2 p-4", mirror && "sm:items-end sm:text-right")}>
      <div className={cn("flex items-center gap-2", mirror && "sm:flex-row-reverse")}>
        <Avatar avatarKey={p?.user.avatar_key} username={p?.user.username} size={28} />
        <div className={cn(mirror && "text-right")}>
          <p className="font-display truncate text-sm">{p?.user.username ?? "—"}</p>
          {win && <span className="font-display text-[9px] uppercase text-[var(--color-accent)]">Vencedor</span>}
        </div>
      </div>
      <div className={cn("flex", mirror && "justify-end")}>
        <DeckSlot sel={sel} reduce={reduce} />
      </div>
    </div>
  );
}

/** Face-down until the selection is revealed, then flips to the deck art. */
function DeckSlot({ sel, reduce }: { sel?: RosterMatchSelection; reduce: boolean }) {
  const revealed = !!sel?.deck;
  return (
    <motion.div
      className="relative h-40 w-28 overflow-hidden rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-3)]"
      initial={false}
      animate={revealed && !reduce ? { rotateY: [90, 0] } : {}}
      transition={{ duration: 0.4 }}
      style={{ transformStyle: "preserve-3d" }}
    >
      {revealed ? (
        <>
          {sel!.deck!.cover_image ? (
            <img src={sel!.deck!.cover_image} alt="" className="h-full w-full object-cover" />
          ) : (
            <div className="grid h-full w-full place-items-center text-[var(--color-ink-subtle)]">
              <Swords className="h-6 w-6" />
            </div>
          )}
          <div className="absolute inset-0 bg-gradient-to-t from-black/85 to-transparent" />
          {sel!.deck!.is_ace && <AceSeal variant="corner" />}
          <p className="absolute inset-x-0 bottom-0 truncate p-1.5 text-center font-display text-[11px] text-white">
            {sel!.deck!.label}
          </p>
        </>
      ) : (
        <div className="grid h-full w-full place-items-center bg-[repeating-linear-gradient(45deg,var(--color-surface-3),var(--color-surface-3)_8px,var(--color-surface-2)_8px,var(--color-surface-2)_16px)]">
          <span className="grid h-9 w-9 place-items-center rounded-full border-2 border-[var(--color-violet)] text-[var(--color-violet)]">
            {sel?.confirmed ? <Crown className="h-4 w-4" /> : "?"}
          </span>
        </div>
      )}
    </motion.div>
  );
}

function PickRow({
  options, myDecks, current, onPick, busy,
}: {
  options?: { uuid: string; label: string; is_ace: boolean }[];
  myDecks?: RosterDeck[];
  current?: string;
  onPick?: (uuid: string) => void;
  busy?: boolean;
}) {
  const items = options ?? (myDecks ?? []).map((d) => ({ uuid: d.uuid, label: d.label, is_ace: d.is_ace }));
  if (!items.length) return null;
  return (
    <div className="mb-2">
      <p className="font-display mb-1.5 text-[10px] uppercase text-[var(--color-ink-muted)]">
        {options ? "Escolha um dos sorteados" : "Escolha seu deck (secreto)"}
      </p>
      <div className="flex flex-wrap gap-1.5">
        {items.map((d) => (
          <Button
            key={d.uuid}
            size="sm"
            variant={current === d.uuid ? "primary" : "secondary"}
            loading={busy}
            onClick={() => onPick?.(d.uuid)}
          >
            {d.is_ace && <Crown className="h-3 w-3" />} {d.label}
          </Button>
        ))}
      </div>
    </div>
  );
}
