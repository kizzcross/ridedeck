import { useState } from "react";
import { Check, Crown, Flag } from "lucide-react";
import type { Match, Participant } from "@/api/tournaments";
import { Avatar } from "@/components/Avatar";
import { cn } from "@/lib/cn";

function Side({
  p,
  score,
  isWinner,
}: {
  p: Participant | null;
  score: number;
  isWinner: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 px-2 py-1.5",
        isWinner ? "bg-[var(--color-accent)]/15" : "",
      )}
    >
      {p ? (
        <>
          <span className="font-display w-4 shrink-0 text-[9px] text-[var(--color-ink-subtle)]">{p.seed ?? "–"}</span>
          <Avatar avatarKey={p.user.avatar_key} username={p.user.username} size={20} />
          <span className={cn("min-w-0 flex-1 truncate text-xs", isWinner ? "font-bold" : "")}>
            {p.user.username}
          </span>
          {isWinner && <Crown className="h-3.5 w-3.5 text-[var(--color-accent)]" />}
          <span className="font-display w-5 text-right text-sm">{score}</span>
        </>
      ) : (
        <span className="px-1 text-[11px] italic text-[var(--color-ink-subtle)]">— a definir —</span>
      )}
    </div>
  );
}

export function MatchCard({
  match,
  canReport,
  canConfirm,
  isOrganizer,
  highlight,
  onReport,
  onConfirm,
  onSetResult,
  onHover,
}: {
  match: Match;
  canReport: boolean;
  canConfirm: boolean;
  isOrganizer: boolean;
  highlight?: boolean;
  onReport: (a: number, b: number) => void;
  onConfirm: () => void;
  onSetResult: (a: number, b: number) => void;
  onHover?: (uuids: string[]) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [a, setA] = useState(match.score_a);
  const [b, setB] = useState(match.score_b);
  const winA = match.winner_uuid && match.participant_a?.uuid === match.winner_uuid;
  const winB = match.winner_uuid && match.participant_b?.uuid === match.winner_uuid;

  const stateBadge = {
    pending: null,
    reported: <span className="text-[var(--color-warning)]">reportado</span>,
    disputed: <span className="text-[var(--color-danger)]">disputa</span>,
    bye: <span className="text-[var(--color-ink-subtle)]">bye</span>,
    done: <span className="text-[var(--color-success)]">final</span>,
  }[match.state];

  const ids = [match.participant_a?.uuid, match.participant_b?.uuid].filter(Boolean) as string[];

  return (
    <div
      className={cn(
        "w-56 overflow-hidden rounded-[6px] border-2 bg-[var(--color-surface)] shadow-[var(--shadow-hard-sm)] transition-colors",
        highlight ? "border-[var(--color-accent)]" : "border-[var(--color-border)]",
      )}
      onMouseEnter={() => onHover?.(ids)}
      onMouseLeave={() => onHover?.([])}
    >
      <div className="flex items-center justify-between border-b-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-0.5">
        <span className="font-display text-[9px] uppercase text-[var(--color-ink-subtle)]">
          {match.table_number ? `Mesa ${match.table_number}` : `#${match.position + 1}`}
        </span>
        <span className="font-display text-[9px] uppercase">{stateBadge}</span>
      </div>
      <Side p={match.participant_a} score={match.score_a} isWinner={!!winA} />
      <div className="h-px bg-[var(--color-border)]" />
      <Side p={match.participant_b} score={match.score_b} isWinner={!!winB} />

      {(canReport || canConfirm || isOrganizer) && match.state !== "done" && match.state !== "bye" &&
        match.participant_a && match.participant_b && (
          <div className="border-t-2 border-[var(--color-border)] p-1.5">
            {editing || (isOrganizer && match.state !== "reported") ? (
              <div className="flex items-center gap-1">
                <input type="number" min={0} value={a} onChange={(e) => setA(+e.target.value)}
                  className="h-7 w-10 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] text-center text-xs" />
                <span className="text-xs">×</span>
                <input type="number" min={0} value={b} onChange={(e) => setB(+e.target.value)}
                  className="h-7 w-10 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] text-center text-xs" />
                <button
                  onClick={() => { (isOrganizer && match.state !== "reported" ? onSetResult : onReport)(a, b); setEditing(false); }}
                  className="font-display ml-auto rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-accent)] px-2 py-1 text-[10px] uppercase text-[#1a1400]"
                >
                  {isOrganizer && match.state !== "reported" ? "Definir" : "Reportar"}
                </button>
              </div>
            ) : match.state === "reported" ? (
              <div className="flex items-center gap-1">
                <span className="text-[10px] text-[var(--color-ink-muted)]">
                  {match.score_a}×{match.score_b} reportado
                </span>
                {canConfirm && (
                  <button onClick={onConfirm}
                    className="font-display ml-auto flex items-center gap-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-success)] px-2 py-1 text-[10px] uppercase text-[#052012]">
                    <Check className="h-3 w-3" /> Confirmar
                  </button>
                )}
                {isOrganizer && (
                  <button onClick={() => setEditing(true)}
                    className="font-display rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-2 py-1 text-[10px] uppercase">
                    Ajustar
                  </button>
                )}
              </div>
            ) : canReport ? (
              <button onClick={() => setEditing(true)}
                className="font-display flex w-full items-center justify-center gap-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] py-1 text-[10px] uppercase">
                <Flag className="h-3 w-3" /> Reportar resultado
              </button>
            ) : null}
          </div>
        )}
    </div>
  );
}
