import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MessageSquare, Send, Trash2 } from "lucide-react";
import { commentsApi, type CommentTarget } from "@/api/comments";
import { Avatar } from "@/components/Avatar";
import { Button, Panel, Skeleton, useToast } from "@/components/ui";
import { useAuth } from "@/hooks/useAuth";
import { apiErrorMessage } from "@/lib/api";
import { cn } from "@/lib/cn";

function timeAgo(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "agora";
  if (diff < 3600) return `${Math.floor(diff / 60)}min`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  if (diff < 604800) return `${Math.floor(diff / 86400)}d`;
  return new Date(iso).toLocaleDateString("pt-BR");
}

/**
 * Generic comment thread — drop it onto any object by passing its
 * `targetType` + `targetUuid`. Powers the community layer across decks,
 * banlists, cards, tournaments and profiles from a single component.
 */
export function CommentThread({
  targetType,
  targetUuid,
  className,
}: {
  targetType: CommentTarget;
  targetUuid: string;
  className?: string;
}) {
  const { user } = useAuth();
  const toast = useToast();
  const qc = useQueryClient();
  const [body, setBody] = useState("");
  const key = ["comments", targetType, targetUuid];

  const { data: comments, isLoading } = useQuery({
    queryKey: key,
    queryFn: () => commentsApi.list(targetType, targetUuid),
    enabled: !!targetUuid,
  });

  const add = useMutation({
    mutationFn: (text: string) => commentsApi.create(targetType, targetUuid, text),
    onSuccess: () => {
      setBody("");
      qc.invalidateQueries({ queryKey: key });
    },
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const del = useMutation({
    mutationFn: (uuid: string) => commentsApi.remove(uuid),
    onSuccess: () => qc.invalidateQueries({ queryKey: key }),
    onError: (e) => toast.error("Erro", apiErrorMessage(e)),
  });

  const submit = () => {
    const text = body.trim();
    if (text) add.mutate(text);
  };

  const list = comments ?? [];

  return (
    <Panel className={cn("p-4", className)}>
      <h3 className="font-display mb-3 flex items-center gap-2 text-sm uppercase text-[var(--color-ink-muted)]">
        <MessageSquare className="h-4 w-4" /> Comentários ({list.length})
      </h3>

      {user && (
        <div className="mb-4 flex items-start gap-2">
          <Avatar avatarKey={user.profile.avatar_key} username={user.username} size={32} />
          <div className="flex-1">
            <textarea
              value={body}
              onChange={(e) => setBody(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit();
              }}
              placeholder="Escreva um comentário…"
              rows={2}
              maxLength={2000}
              className="w-full resize-y rounded-[var(--radius-card)] border-2 border-[var(--color-border)] bg-[var(--color-surface-2)] px-3 py-2 text-sm focus:border-[var(--color-accent)] focus:outline-none"
            />
            <div className="mt-1.5 flex justify-end">
              <Button size="sm" loading={add.isPending} disabled={!body.trim()} onClick={submit}>
                <Send className="h-3.5 w-3.5" /> Enviar
              </Button>
            </div>
          </div>
        </div>
      )}

      {isLoading ? (
        <Skeleton className="h-16 w-full" />
      ) : list.length === 0 ? (
        <p className="text-sm text-[var(--color-ink-subtle)]">Nenhum comentário ainda. Seja o primeiro!</p>
      ) : (
        <ul className="space-y-3">
          {list.map((c) => (
            <li key={c.uuid} className="flex items-start gap-2">
              <Avatar avatarKey={c.author.avatar_key} username={c.author.username} size={32} />
              <div className="min-w-0 flex-1">
                <div className="flex items-center gap-2">
                  <span className="font-display text-sm">{c.author.display_name || c.author.username}</span>
                  {c.author.is_platform_admin && (
                    <span className="rounded-[4px] bg-[var(--color-accent)] px-1.5 text-[10px] font-bold uppercase text-[#1a1400]">
                      admin
                    </span>
                  )}
                  <span className="text-xs text-[var(--color-ink-subtle)]">{timeAgo(c.created_at)}</span>
                  {c.can_delete && (
                    <button
                      aria-label="Remover comentário"
                      onClick={() => del.mutate(c.uuid)}
                      className="ml-auto text-[var(--color-ink-subtle)] hover:text-[var(--color-danger)]"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  )}
                </div>
                <p className="whitespace-pre-wrap break-words text-sm text-[var(--color-ink-muted)]">{c.body}</p>
              </div>
            </li>
          ))}
        </ul>
      )}
    </Panel>
  );
}
