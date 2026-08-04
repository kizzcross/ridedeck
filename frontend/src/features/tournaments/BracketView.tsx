import { useState } from "react";
import { Minus, Plus } from "lucide-react";
import type { Match, Stage } from "@/api/tournaments";
import { MatchCard } from "./MatchCard";
import { Button } from "@/components/ui";

export function BracketView({
  stages,
  currentUserId,
  isOrganizer,
  onReport,
  onConfirm,
  onSetResult,
}: {
  stages: Stage[];
  currentUserId?: string;
  isOrganizer: boolean;
  onReport: (m: Match, a: number, b: number) => void;
  onConfirm: (m: Match) => void;
  onSetResult: (m: Match, a: number, b: number) => void;
}) {
  const [zoom, setZoom] = useState(1);
  const [highlight, setHighlight] = useState<string[]>([]);
  const stage = stages[0];
  if (!stage) return <p className="text-sm text-[var(--color-ink-subtle)]">Bracket ainda não gerado.</p>;

  const isMine = (m: Match) =>
    !!currentUserId &&
    [m.participant_a?.user.uuid, m.participant_b?.user.uuid].includes(currentUserId);

  return (
    <div className="relative">
      <div className="absolute right-0 top-0 z-10 flex gap-1">
        <Button size="icon" variant="secondary" aria-label="Menos zoom" onClick={() => setZoom((z) => Math.max(0.6, z - 0.1))}>
          <Minus className="h-4 w-4" />
        </Button>
        <Button size="icon" variant="secondary" aria-label="Mais zoom" onClick={() => setZoom((z) => Math.min(1.4, z + 0.1))}>
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      <div className="overflow-x-auto pb-4 pt-10">
        <div
          className="flex origin-top-left gap-8"
          style={{ transform: `scale(${zoom})`, width: `${100 / zoom}%` }}
        >
          {stage.rounds.map((round) => (
            <div key={round.uuid} className="flex min-w-[15rem] flex-col">
              <h4 className="font-display mb-3 text-center text-[11px] uppercase tracking-wide text-[var(--color-ink-muted)]">
                {round.name}
              </h4>
              <div className="flex flex-1 flex-col justify-around gap-4">
                {round.matches.map((m) => {
                  const mine = isMine(m);
                  const reporterIsMe = false; // reported_by not surfaced; opponent-confirm handled server-side
                  return (
                    <MatchCard
                      key={m.uuid}
                      match={m}
                      canReport={mine && m.state === "pending"}
                      canConfirm={mine && m.state === "reported" && !reporterIsMe}
                      isOrganizer={isOrganizer}
                      highlight={highlight.length > 0 &&
                        [m.participant_a?.uuid, m.participant_b?.uuid].some((u) => u && highlight.includes(u))}
                      onReport={(a, b) => onReport(m, a, b)}
                      onConfirm={() => onConfirm(m)}
                      onSetResult={(a, b) => onSetResult(m, a, b)}
                      onHover={setHighlight}
                    />
                  );
                })}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
