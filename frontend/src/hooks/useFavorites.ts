import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { socialApi } from "@/api/social";
import { useAuth } from "./useAuth";

/** Favorite-card state for the current user: a Set of favorited card uuids plus
 *  an optimistic toggle. */
export function useFavorites() {
  const qc = useQueryClient();
  const authed = useAuth((s) => s.status === "authenticated");

  const { data: ids } = useQuery({
    queryKey: ["favorite-ids"],
    queryFn: socialApi.favoriteIds,
    enabled: authed,
    staleTime: 60_000,
  });

  const set = new Set(ids ?? []);

  const toggle = useCallback(
    async (cardUuid: string) => {
      // optimistic
      const prev = qc.getQueryData<string[]>(["favorite-ids"]) ?? [];
      const isFav = prev.includes(cardUuid);
      const next = isFav ? prev.filter((u) => u !== cardUuid) : [...prev, cardUuid];
      qc.setQueryData(["favorite-ids"], next);
      try {
        await socialApi.toggleFavorite(cardUuid);
        qc.invalidateQueries({ queryKey: ["favorites"] });
      } catch {
        qc.setQueryData(["favorite-ids"], prev); // revert
      }
    },
    [qc],
  );

  return { isFavorite: (uuid: string) => set.has(uuid), toggle, favoriteIds: set };
}
