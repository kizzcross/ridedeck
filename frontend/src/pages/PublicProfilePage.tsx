import { useParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, UserPlus, UserCheck, X } from "lucide-react";
import { profileApi, socialApi } from "@/api/social";
import { useAuth } from "@/hooks/useAuth";
import { Avatar } from "@/components/Avatar";
import { Badge, Button, Panel, Skeleton, useToast } from "@/components/ui";
import { apiErrorMessage } from "@/lib/api";

export function PublicProfilePage() {
  const { username = "" } = useParams();
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();

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

  if (isLoading || !profile) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  const isSelf = profile.friendship_state === "self" || user?.username === username;

  return (
    <div className="mx-auto max-w-2xl">
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
    </div>
  );
}
