import { useMemo } from "react";
import { useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { tournamentsApi, type RosterRound } from "@/api/tournaments";
import { VersusBoard } from "@/features/championship/VersusBoard";

/** A chrome-free versus overlay for streaming (OBS browser source). Shows the
 *  featured active match; opponent decks stay hidden until the reveal, so it never
 *  leaks picks on stream. Public tournaments only. */
export function OverlayPage() {
  const { uuid = "" } = useParams();
  const { data: t } = useQuery({ queryKey: ["overlay-t", uuid], queryFn: () => tournamentsApi.detail(uuid) });
  const { data: rounds } = useQuery({
    queryKey: ["overlay-rounds", uuid], queryFn: () => tournamentsApi.rosterRounds(uuid),
    refetchInterval: 4000,
  });

  const round: RosterRound | undefined = useMemo(
    () => rounds && [...rounds].reverse().find((r) => r.status === "active"),
    [rounds],
  );
  const match = round?.matches.find((m) => m.state !== "done" && m.state !== "bye") ?? round?.matches[0];

  return (
    <div className="grid min-h-dvh place-items-center bg-[var(--color-bg,#0b0a14)] p-6">
      <div className="w-full max-w-3xl">
        {t && <p className="mb-3 text-center font-display text-lg text-[var(--color-accent)]">{t.name}{round ? ` · ${round.name || `Rodada ${round.number}`}` : ""}</p>}
        {match ? (
          <div className="scale-105">
            <VersusBoard match={match} />
          </div>
        ) : (
          <p className="text-center font-display text-[var(--color-ink-muted)]">Aguardando a próxima partida…</p>
        )}
      </div>
    </div>
  );
}
