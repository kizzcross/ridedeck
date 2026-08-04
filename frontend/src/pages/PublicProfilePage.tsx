import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Heart, Layers, Ban, MessageSquare, UserPlus, UserCheck, X } from "lucide-react";
import { profileApi, socialApi } from "@/api/social";
import { decksApi } from "@/api/decks";
import { banlistsApi } from "@/api/banlists";
import { useAuth } from "@/hooks/useAuth";
import { Avatar } from "@/components/Avatar";
import { CardArt } from "@/features/catalog/CardArt";
import { CommentThread } from "@/components/CommentThread";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { cn } from "@/lib/cn";
import { apiErrorMessage } from "@/lib/api";

type ProfileTab = "decks" | "banlists" | "favorites" | "comments";

export function PublicProfilePage() {
  const { username = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [tab, setTab] = useState<ProfileTab>("decks");

  const { data: profile, isLoading } = useQuery({
    queryKey: ["public-profile", username],
    queryFn: () => profileApi.publicProfile(username),
  });

  const invalidate = () => qc.invalidateQueries({ queryKey: ["public-profile", username] });

  const add = useMutation({
    mutationFn: () => socialApi.addFriend(username),
    onSuccess: () => { invalidate(); toast.success("Solicitação enviada"); },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });
  const accept = useMutation({
    mutationFn: (uuid: string) => socialApi.acceptFriend(uuid),
    onSuccess: () => { invalidate(); toast.success("Agora vocês são amigos"); },
  });
  const remove = useMutation({
    mutationFn: (uuid: string) => socialApi.removeFriend(uuid),
    onSuccess: invalidate,
  });

  const decksQ = useQuery({
    queryKey: ["profile-decks", username],
    queryFn: () => decksApi.publicDecks({ owner: username, page_size: 60 }),
    enabled: !!username && tab === "decks",
  });
  const banlistsQ = useQuery({
    queryKey: ["profile-banlists", username],
    queryFn: () => banlistsApi.list({ owner: username }),
    enabled: !!username && tab === "banlists",
  });
  const favoritesQ = useQuery({
    queryKey: ["profile-favorites", username],
    queryFn: () => profileApi.userFavoriteCards(username),
    enabled: !!username && tab === "favorites",
  });

  if (isLoading || !profile) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const isSelf = profile.friendship_state === "self" || user?.username === username;

  const TABS: { key: ProfileTab; label: string; icon: typeof Layers }[] = [
    { key: "decks", label: "Decks", icon: Layers },
    { key: "banlists", label: "Banlists", icon: Ban },
    { key: "favorites", label: "Favoritas", icon: Heart },
    { key: "comments", label: "Mural", icon: MessageSquare },
  ];

  return (
    <div className="mx-auto max-w-4xl space-y-5">
      <Panel className="p-6">
        <div className="flex flex-col items-center gap-4 sm:flex-row">
          <Avatar avatarKey={profile.profile.avatar_key} username={profile.username} size={80} />
          <div className="flex-1 text-center sm:text-left">
            <h1 className="font-display text-2xl">{profile.username}</h1>
            {profile.profile.display_name && (
              <p className="text-sm text-[var(--color-ink-muted)]">{profile.profile.display_name}</p>
            )}
            <div className="mt-2 flex flex-wrap justify-center gap-2 sm:justify-start">
              <Badge tone={profile.role === "platform_admin" ? "official" : "neutral"}>
                {profile.role === "platform_admin" ? "Platform Admin" : "Membro"}
              </Badge>
              <Badge tone="brand">{profile.friend_count} amigos</Badge>
            </div>
          </div>

          {!isSelf && (
            <div>
              {profile.friendship_state === "none" && (
                <Button loading={add.isPending} onClick={() => add.mutate()}>
                  <UserPlus className="h-4 w-4" /> Adicionar
                </Button>
              )}
              {profile.friendship_state === "outgoing" && (
                <Button variant="outline" onClick={() => profile.friendship_uuid && remove.mutate(profile.friendship_uuid)}>
                  <X className="h-4 w-4" /> Cancelar
                </Button>
              )}
              {profile.friendship_state === "incoming" && profile.friendship_uuid && (
                <div className="flex gap-2">
                  <Button onClick={() => accept.mutate(profile.friendship_uuid!)}>
                    <Check className="h-4 w-4" /> Aceitar
                  </Button>
                  <Button variant="ghost" onClick={() => remove.mutate(profile.friendship_uuid!)}>
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              )}
              {profile.friendship_state === "friend" && (
                <Button variant="secondary" onClick={() => profile.friendship_uuid && remove.mutate(profile.friendship_uuid)}>
                  <UserCheck className="h-4 w-4" /> Amigos
                </Button>
              )}
            </div>
          )}
        </div>
        {profile.profile.bio && (
          <p className="mt-4 whitespace-pre-line text-sm text-[var(--color-ink-muted)]">{profile.profile.bio}</p>
        )}
      </Panel>

      {/* Community tabs */}
      <div className="flex flex-wrap gap-1.5">
        {TABS.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              "font-display flex items-center gap-1.5 rounded-[var(--radius-card)] border-2 px-3 py-1.5 text-[11px] uppercase",
              tab === key
                ? "border-[var(--color-border)] bg-[var(--color-accent)] text-[#1a1400]"
                : "border-[var(--color-border)] bg-[var(--color-surface-2)] text-[var(--color-ink-muted)]",
            )}
          >
            <Icon className="h-4 w-4" /> {label}
          </button>
        ))}
      </div>

      {tab === "decks" && (
        decksQ.isLoading ? <Skeleton className="h-32 w-full" /> :
        !decksQ.data?.results.length ? <Empty>Nenhum deck público.</Empty> : (
          <div className="grid gap-3 sm:grid-cols-2">
            {decksQ.data.results.map((d) => (
              <Link key={d.uuid} to={`/app/decks/${d.uuid}/view`}>
                <Panel className="flex items-center justify-between p-4 transition hover:border-[var(--color-accent)]">
                  <div className="min-w-0">
                    <p className="font-display truncate">{d.title}</p>
                    <p className="text-xs text-[var(--color-ink-subtle)]">
                      {d.format_code} · {d.main_count} cartas · ♥ {d.like_count}
                    </p>
                  </div>
                  {d.archetype && <Badge tone="neutral">{d.archetype}</Badge>}
                </Panel>
              </Link>
            ))}
          </div>
        )
      )}

      {tab === "banlists" && (
        banlistsQ.isLoading ? <Skeleton className="h-32 w-full" /> :
        !banlistsQ.data?.results.length ? <Empty>Nenhuma banlist pública.</Empty> : (
          <div className="grid gap-3 sm:grid-cols-2">
            {banlistsQ.data.results.map((b) => (
              <Link key={b.uuid} to={`/app/banlists/${b.uuid}`}>
                <Panel className="flex items-center justify-between p-4 transition hover:border-[var(--color-accent)]">
                  <div className="min-w-0">
                    <p className="font-display truncate">{b.name}</p>
                    <p className="text-xs text-[var(--color-ink-subtle)]">
                      {b.format_code} · {b.entry_count} restrições
                    </p>
                  </div>
                  {b.is_official && <Badge tone="official">Oficial</Badge>}
                </Panel>
              </Link>
            ))}
          </div>
        )
      )}

      {tab === "favorites" && (
        favoritesQ.isLoading ? <Skeleton className="h-32 w-full" /> :
        !favoritesQ.data?.length ? <Empty>Nenhuma carta favorita pública.</Empty> : (
          <div className="grid grid-cols-3 gap-2 sm:grid-cols-4 md:grid-cols-6">
            {favoritesQ.data.map((f) => (
              <CardArt key={f.uuid} card={f.card} />
            ))}
          </div>
        )
      )}

      {tab === "comments" && <CommentThread targetType="profile" targetUuid={profile.uuid} />}
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <Panel className="p-8 text-center text-sm text-[var(--color-ink-subtle)]">{children}</Panel>
  );
}
