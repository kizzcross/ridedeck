import { Construction } from "lucide-react";
import { Badge, Panel } from "@/components/ui";

/** Honest placeholder: this surface is scaffolded and routed, but its features
 *  ship in the phase indicated. Not a fake mock — it names what's coming. */
export function PhasePlaceholder({
  title,
  phase,
  bullets,
}: {
  title: string;
  phase: string;
  bullets: string[];
}) {
  return (
    <div className="mx-auto max-w-2xl">
      <Panel className="p-8 text-center">
        <div className="mx-auto mb-4 grid h-14 w-14 place-items-center rounded-2xl bg-[var(--color-surface-2)]">
          <Construction className="h-7 w-7 text-[var(--color-accent)]" />
        </div>
        <Badge tone="brand" className="mx-auto mb-3">
          {phase}
        </Badge>
        <h1 className="font-display text-2xl font-bold">{title}</h1>
        <p className="mt-2 text-sm text-[var(--color-ink-muted)]">
          Esta área está roteada e faz parte da fundação. Os recursos abaixo chegam nesta fase.
        </p>
        <ul className="mx-auto mt-5 max-w-md space-y-2 text-left">
          {bullets.map((b) => (
            <li key={b} className="flex items-start gap-2 text-sm text-[var(--color-ink-muted)]">
              <span className="mt-1 h-1.5 w-1.5 shrink-0 rounded-full bg-[var(--color-accent)]" />
              {b}
            </li>
          ))}
        </ul>
      </Panel>
    </div>
  );
}
