import { useState } from "react";
import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Copy, UserPlus, X, Users, Heart, ShieldPlus } from "lucide-react";
import { profileApi, socialApi, type AvatarOption } from "@/api/social";
import { useAuth } from "@/hooks/useAuth";
import { Avatar } from "@/components/Avatar";
import { NationLogo } from "@/components/NationLogo";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { CardTile } from "@/features/catalog/CardTile";
import { CardDetailDrawer } from "@/features/catalog/CardDetailDrawer";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

function SectionTitle({ icon: Icon, children }: { icon: React.ElementType; children: React.ReactNode }) {
  return (
    <h2 className="font-display mb-3 flex items-center gap-2 text-sm uppercase tracking-wide text-[var(--color-ink-muted)]">
      <Icon className="h-4 w-4 text-[var(--color-accent)]" />
      {children}
    </h2>
  );
}

export function ProfilePage() {
  const { user, refreshUser } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [copied, setCopied] = useState(false);
  const [addName, setAddName] = useState("");
  const [openSlug, setOpenSlug] = useState<string | null>(null);

  const { data: avatarOptions } = useQuery({ queryKey: ["avatar-options"], queryFn: socialApi.avatarOptions });
  const { data: friends } = useQuery({ queryKey: ["friends"], queryFn: socialApi.friends });
  const { data: requests } = useQuery({ queryKey: ["friend-requests"], queryFn: socialApi.requests });
  const { data: favorites } = useQuery({ queryKey: ["favorites"], queryFn: socialApi.favorites });

  const setAvatar = useMutation({
    mutationFn: (key: string) => profileApi.updateProfile({ avatar_key: key }),
    onSuccess: async () => {
      await refreshUser();
      toast.success("Avatar atualizado");
    },
  });

  const addFriend = useMutation({
    mutationFn: (username: string) => socialApi.addFriend(username),
    onSuccess: () => {
      setAddName("");
      qc.invalidateQueries({ queryKey: ["friend-requests"] });
      qc.invalidateQueries({ queryKey: ["friends"] });
      toast.success("Solicitação enviada");
    },
    onError: (e) => toast.error("Não foi possível adicionar", apiErrorMessage(e)),
  });

  const respond = useMutation({
    mutationFn: async ({ uuid, accept }: { uuid: string; accept: boolean }) => {
      if (accept) await socialApi.acceptFriend(uuid);
      else await socialApi.removeFriend(uuid);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["friend-requests"] });
      qc.invalidateQueries({ queryKey: ["friends"] });
    },
  });

  const promote = useMutation({
    mutationFn: (username: string) => socialApi.promoteToAdmin(username),
    onSuccess: (d) => {
      qc.invalidateQueries({ queryKey: ["friends"] });
      toast.success(`${d.username} agora é Platform Admin`);
    },
    onError: (e) => toast.error("Não foi possível promover", apiErrorMessage(e)),
  });

  if (!user) return null;
  const referralLink = `${window.location.origin}/register?ref=${user.profile.referral_code ?? ""}`;

  const copy = async () => {
    await navigator.clipboard.writeText(referralLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Panel className="flex flex-col items-center gap-4 p-6 sm:flex-row sm:items-center">
        <Avatar avatarKey={user.profile.avatar_key} username={user.username} size={72} />
        <div className="flex-1 text-center sm:text-left">
          <h1 className="font-display text-2xl">{user.username}</h1>
          <div className="mt-1 flex flex-wrap justify-center gap-2 sm:justify-start">
            <Badge tone={user.is_platform_admin ? "official" : "neutral"}>
              {user.is_platform_admin ? "Platform Admin" : "Membro"}
            </Badge>
            <Badge tone="brand">{user.friend_count} amigos</Badge>
            <Badge tone="accent">{favorites?.count ?? 0} favoritas</Badge>
          </div>
        </div>
      </Panel>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Avatar picker */}
        <Panel className="p-5">
          <SectionTitle icon={Users}>Escolher avatar (logo de nation)</SectionTitle>
          <div className="grid grid-cols-6 gap-2">
            {(avatarOptions ?? []).map((opt: AvatarOption) => {
              const active = user.profile.avatar_key === opt.key;
              return (
                <button
                  key={opt.key}
                  onClick={() => setAvatar.mutate(opt.key)}
                  title={opt.label}
                  aria-label={opt.label}
                  aria-pressed={active}
                  className={cn(
                    "rd-press grid aspect-square place-items-center rounded-[6px] border-2",
                    active
                      ? "border-[var(--color-accent)] bg-[var(--color-accent)]/15"
                      : "border-[var(--color-border)] bg-[var(--color-surface-2)] hover:bg-[var(--color-surface-3)]",
                  )}
                >
                  <NationLogo nation={opt.nation} size={22} />
                </button>
              );
            })}
          </div>
        </Panel>

        {/* Referral */}
        <Panel className="p-5">
          <SectionTitle icon={UserPlus}>Seu link de convite</SectionTitle>
          <p className="mb-2 text-xs text-[var(--color-ink-muted)]">
            Quem entrar por este link já vira seu amigo automaticamente.
          </p>
          <div className="flex gap-2">
            <input
              readOnly
              value={referralLink}
              onFocus={(e) => e.target.select()}
              className="h-10 flex-1 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 text-xs"
            />
            <Button variant="secondary" onClick={copy}>
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
              {copied ? "Copiado" : "Copiar"}
            </Button>
          </div>
          <p className="font-display mt-3 text-[10px] uppercase text-[var(--color-ink-subtle)]">
            Código: {user.profile.referral_code}
          </p>
        </Panel>

        {/* Friends */}
        <Panel className="p-5">
          <SectionTitle icon={Users}>Amigos ({friends?.length ?? 0})</SectionTitle>
          <div className="mb-3 flex gap-2">
            <input
              value={addName}
              onChange={(e) => setAddName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && addName && addFriend.mutate(addName)}
              placeholder="Adicionar por username…"
              className="h-9 flex-1 rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface)] px-3 text-sm"
            />
            <Button size="sm" loading={addFriend.isPending} disabled={!addName}
              onClick={() => addFriend.mutate(addName)}>
              <UserPlus className="h-4 w-4" />
            </Button>
          </div>
          {friends === undefined ? (
            <Skeleton className="h-16 w-full" />
          ) : friends.length === 0 ? (
            <p className="text-sm text-[var(--color-ink-subtle)]">Nenhum amigo ainda.</p>
          ) : (
            <ul className="space-y-1.5">
              {friends.map((f) => (
                <li key={f.uuid} className="flex items-center gap-2">
                  <Avatar avatarKey={f.avatar_key} username={f.username} size={32} />
                  <Link to={`/app/u/${f.username}`} className="flex-1 truncate text-sm font-medium hover:text-[var(--color-accent)]">
                    {f.username}
                  </Link>
                  {f.is_platform_admin ? (
                    <Badge tone="official">Admin</Badge>
                  ) : (
                    user.is_platform_admin && (
                      <Button
                        size="sm"
                        variant="ghost"
                        title="Tornar Platform Admin"
                        loading={promote.isPending && promote.variables === f.username}
                        onClick={() => promote.mutate(f.username)}
                      >
                        <ShieldPlus className="h-4 w-4" />
                      </Button>
                    )
                  )}
                </li>
              ))}
            </ul>
          )}
        </Panel>

        {/* Requests */}
        <Panel className="p-5">
          <SectionTitle icon={UserPlus}>Solicitações</SectionTitle>
          <p className="font-display mb-1 text-[10px] uppercase text-[var(--color-ink-subtle)]">Recebidas</p>
          {requests?.incoming.length ? (
            <ul className="mb-3 space-y-1.5">
              {requests.incoming.map((r) => (
                <li key={r.uuid} className="flex items-center gap-2">
                  <Avatar avatarKey={r.requester.avatar_key} username={r.requester.username} size={30} />
                  <span className="flex-1 text-sm">{r.requester.username}</span>
                  <Button size="sm" onClick={() => respond.mutate({ uuid: r.uuid, accept: true })}>
                    <Check className="h-3.5 w-3.5" />
                  </Button>
                  <Button size="sm" variant="ghost" onClick={() => respond.mutate({ uuid: r.uuid, accept: false })}>
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="mb-3 text-sm text-[var(--color-ink-subtle)]">Nenhuma.</p>
          )}
          <p className="font-display mb-1 text-[10px] uppercase text-[var(--color-ink-subtle)]">Enviadas</p>
          {requests?.outgoing.length ? (
            <ul className="space-y-1.5">
              {requests.outgoing.map((r) => (
                <li key={r.uuid} className="flex items-center gap-2">
                  <Avatar avatarKey={r.addressee.avatar_key} username={r.addressee.username} size={30} />
                  <span className="flex-1 text-sm">{r.addressee.username}</span>
                  <Badge tone="warning">pendente</Badge>
                  <Button size="sm" variant="ghost" onClick={() => respond.mutate({ uuid: r.uuid, accept: false })}>
                    <X className="h-3.5 w-3.5" />
                  </Button>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--color-ink-subtle)]">Nenhuma.</p>
          )}
        </Panel>
      </div>

      {/* Favorites */}
      <Panel className="p-5">
        <SectionTitle icon={Heart}>Cartas favoritas ({favorites?.count ?? 0})</SectionTitle>
        {favorites === undefined ? (
          <Skeleton className="h-32 w-full" />
        ) : favorites.results.length === 0 ? (
          <p className="text-sm text-[var(--color-ink-subtle)]">
            Nenhuma favorita ainda — passe o mouse numa carta do catálogo e clique no ♥.
          </p>
        ) : (
          <div className="grid grid-cols-3 gap-3 sm:grid-cols-5 xl:grid-cols-8">
            {favorites.results.map((fav) => (
              <CardTile key={fav.uuid} card={fav.card} onOpen={(c) => setOpenSlug(c.slug)} />
            ))}
          </div>
        )}
      </Panel>

      <CardDetailDrawer slug={openSlug} onClose={() => setOpenSlug(null)} />
    </div>
  );
}
