import { Link, useNavigate, useParams } from "react-router-dom";
import { useMutation, useQuery } from "@tanstack/react-query";
import { GitFork, Globe, Lock, Link2, Pencil } from "lucide-react";
import { decksApi } from "@/api/decks";
import { Avatar } from "@/components/Avatar";
import { CardArt } from "@/features/catalog/CardArt";
import { ZONES } from "@/features/builder/zones";
import { CommentThread } from "@/components/CommentThread";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

const FORMAT_LABEL: Record<string, string> = {
  standard: "Standard", v_premium: "V Premium", premium: "Premium", g: "G Era",
};

/** Read-only public view of someone else's deck — the community entry point
 *  for browsing + commenting on decks you don't own. */
export function DeckViewPage() {
  const { uuid = "" } = useParams();
  const navigate = useNavigate();
  const toast = useToast();

  const { data: deck, isLoading } = useQuery({
    queryKey: ["deck-view", uuid],
    queryFn: () => decksApi.detail(uuid),
  });

  const fork = useMutation({
    mutationFn: () => decksApi.fork(uuid),
    onSuccess: (d) => { toast.success("Deck copiado para você!"); navigate(`/app/decks/${d.uuid}`); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  if (isLoading || !deck) return <Skeleton className="h-64 w-full" />;

  // Owners edit in the builder; everyone else gets the read-only view.
  if (deck.is_owner) {
    return (
      <div className="mx-auto max-w-md py-16 text-center">
        <p className="mb-4 text-sm text-[var(--color-ink-muted)]">Este deck é seu.</p>
        <Link to={`/app/decks/${uuid}`}><Button><Pencil className="h-4 w-4" /> Editar no builder</Button></Link>
      </div>
    );
  }

  const version = deck.current_version;
  const VisIcon = deck.visibility === "public" ? Globe : deck.visibility === "unlisted" ? Link2 : Lock;

  return (
    <div className="mx-auto max-w-5xl space-y-5">
      <Panel className="p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <div className="mb-1 flex flex-wrap items-center gap-2">
              <Badge tone="brand">{FORMAT_LABEL[deck.format_code] ?? deck.format_code}</Badge>
              {deck.archetype && <Badge tone="neutral">{deck.archetype}</Badge>}
              <Badge tone={deck.visibility === "public" ? "success" : "neutral"}>
                <VisIcon className="h-3 w-3" /> {deck.visibility}
              </Badge>
            </div>
            <h1 className="font-display text-2xl">{deck.title}</h1>
            <Link
              to={`/app/u/${deck.owner.username}`}
              className="mt-2 inline-flex items-center gap-2 text-sm text-[var(--color-ink-muted)] hover:text-[var(--color-ink)]"
            >
              <Avatar avatarKey={deck.owner.avatar_key} username={deck.owner.username} size={24} />
              por {deck.owner.username}
            </Link>
            {deck.description && <p className="mt-2 text-sm text-[var(--color-ink-muted)]">{deck.description}</p>}
          </div>
          <Button variant="secondary" size="sm" loading={fork.isPending} onClick={() => fork.mutate()}>
            <GitFork className="h-4 w-4" /> Copiar deck
          </Button>
        </div>
      </Panel>

      {ZONES.map((z) => {
        const entries = version.entries.filter((e) => e.zone === z.key);
        if (entries.length === 0) return null;
        return (
          <Panel key={z.key} className="p-4">
            <h3 className="font-display mb-3 text-sm uppercase text-[var(--color-ink-muted)]">
              {z.label} ({version.zone_counts[z.key] ?? 0})
            </h3>
            <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6 lg:grid-cols-8">
              {entries.map((e) => (
                <div key={e.uuid} className="relative">
                  <CardArt card={e.card} />
                  {e.quantity > 1 && (
                    <span className="absolute right-1 top-1 rounded-[4px] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-1 font-display text-xs">
                      ×{e.quantity}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </Panel>
        );
      })}

      {deck.guide && (
        <Panel className="p-4">
          <h3 className="font-display mb-2 text-sm uppercase text-[var(--color-ink-muted)]">Guia</h3>
          <p className="whitespace-pre-wrap text-sm text-[var(--color-ink-muted)]">{deck.guide}</p>
        </Panel>
      )}

      <CommentThread targetType="deck" targetUuid={uuid} />
    </div>
  );
}
