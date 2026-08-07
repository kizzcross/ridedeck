import { useQuery } from "@tanstack/react-query";
import { Minus, Plus } from "lucide-react";
import { cardsApi } from "@/api/cards";
import { Badge, Drawer, Skeleton } from "@/components/ui";
import { CardArt } from "./CardArt";
import { FavoriteButton } from "./FavoriteButton";
import { CommentThread } from "@/components/CommentThread";
import { ClanIcon, NationLogo } from "@/components/NationLogo";
import { useOwnedMap } from "@/hooks/useOwnedMap";
import { useAuth } from "@/hooks/useAuth";
import { TRIGGER_LABELS, cardTypeLabel, nationLabel } from "@/lib/cardMeta";

function OwnedControl({ cardUuid, printingUuid }: { cardUuid: string; printingUuid?: string }) {
  const authed = useAuth((s) => s.status === "authenticated");
  const { ownedOf, setOwned } = useOwnedMap();
  if (!authed || !printingUuid) return null;
  const qty = ownedOf(cardUuid);
  return (
    <div className="flex items-center justify-between rounded-[6px] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2">
      <span className="font-display text-[10px] uppercase text-[var(--color-ink-muted)]">Na coleção</span>
      <div className="flex items-center gap-2">
        <button onClick={() => setOwned(printingUuid, Math.max(0, qty - 1))} aria-label="Menos" className="grid h-7 w-7 place-items-center rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface-3)]">
          <Minus className="h-3.5 w-3.5" />
        </button>
        <span className="font-display w-6 text-center">{qty}</span>
        <button onClick={() => setOwned(printingUuid, qty + 1)} aria-label="Mais" className="grid h-7 w-7 place-items-center rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]">
          <Plus className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-lg bg-[var(--color-surface-2)] px-3 py-2">
      <p className="text-[10px] uppercase tracking-wide text-[var(--color-ink-subtle)]">{label}</p>
      <p className="font-display text-sm font-semibold">{value ?? "—"}</p>
    </div>
  );
}

export function CardDetailDrawer({ slug, onClose }: { slug: string | null; onClose: () => void }) {
  const { data: card, isLoading } = useQuery({
    queryKey: ["card", slug],
    queryFn: () => cardsApi.detail(slug!),
    enabled: !!slug,
  });

  return (
    <Drawer open={!!slug} onClose={onClose} title={card?.name ?? "Carta"}>
      {isLoading || !card ? (
        <div className="space-y-3">
          <Skeleton className="mx-auto h-64 w-44" />
          <Skeleton className="h-20 w-full" />
        </div>
      ) : (
        <div className="space-y-4">
          <div className="relative mx-auto w-44">
            <CardArt card={card} />
            <div className="absolute right-1 top-1">
              <FavoriteButton cardUuid={card.uuid} />
            </div>
          </div>

          <div className="flex flex-wrap gap-1.5">
            <Badge tone="brand">Grade {card.grade}</Badge>
            <Badge tone="neutral">{cardTypeLabel(card.card_type)}</Badge>
            {card.trigger && <Badge tone="accent">{TRIGGER_LABELS[card.trigger] ?? card.trigger}</Badge>}
            {card.is_persona_ride && <Badge tone="warning">Persona Ride</Badge>}
          </div>

          <OwnedControl cardUuid={card.uuid} printingUuid={card.default_printing?.uuid} />

          <div className="grid grid-cols-3 gap-2">
            <Stat label="Power" value={card.power?.toLocaleString()} />
            <Stat label="Shield" value={card.shield?.toLocaleString()} />
            <Stat label="Critical" value={card.critical} />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <Stat
              label="Nation"
              value={
                card.nation ? (
                  <span className="flex items-center gap-1.5">
                    <NationLogo nation={card.nation} size={16} />
                    {nationLabel(card.nation)}
                  </span>
                ) : (
                  "—"
                )
              }
            />
            <Stat
              label="Clan"
              value={
                card.clan ? (
                  <span className="flex items-center gap-1.5">
                    <ClanIcon clan={card.clan} size={16} />
                    {card.clan}
                  </span>
                ) : (
                  "—"
                )
              }
            />
          </div>

          {card.ability_text && (
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-subtle)]">
                Habilidade
              </h4>
              <p className="whitespace-pre-line rounded-lg bg-[var(--color-surface-2)] p-3 text-sm text-[var(--color-ink-muted)]">
                {card.ability_text}
              </p>
            </div>
          )}

          {card.format_legalities.length > 0 && (
            <div>
              <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-subtle)]">
                Formatos
              </h4>
              <div className="flex flex-wrap gap-1.5">
                {card.format_legalities.map((f) => (
                  <Badge key={f.format_code} tone={f.legality === "legal" ? "success" : "warning"}>
                    {f.format_code} · {f.legality}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div>
            <h4 className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--color-ink-subtle)]">
              Printings ({card.printings.length})
            </h4>
            <div className="space-y-1.5">
              {card.printings.map((p) => (
                <div
                  key={p.uuid}
                  className="flex items-center justify-between rounded-lg bg-[var(--color-surface-2)] px-3 py-2 text-sm"
                >
                  <div className="min-w-0">
                    <p className="truncate font-medium">{p.card_number}</p>
                    <p className="text-xs text-[var(--color-ink-subtle)]">
                      {p.set_name} · {p.rarity || "—"} · {p.language.toUpperCase()}
                      {p.finish ? ` · ${p.finish}` : ""}
                    </p>
                  </div>
                  {p.price && <span className="font-display text-sm font-semibold">${p.price}</span>}
                </div>
              ))}
            </div>
          </div>

          <CommentThread targetType="card" targetUuid={card.uuid} className="!bg-transparent !border-0 !p-0" />
        </div>
      )}
    </Drawer>
  );
}
