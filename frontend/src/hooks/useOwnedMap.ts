import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback } from "react";
import { collectionApi } from "@/api/collection";
import { useAuth } from "./useAuth";

/** The current user's owned-quantity map ({card_uuid: qty}) plus a helper to
 *  bump ownership for a printing. */
export function useOwnedMap() {
  const qc = useQueryClient();
  const authed = useAuth((s) => s.status === "authenticated");

  const { data: owned } = useQuery({
    queryKey: ["owned-map"],
    queryFn: collectionApi.ownedMap,
    enabled: authed,
    staleTime: 60_000,
  });

  const ownedOf = useCallback((cardUuid: string) => owned?.[cardUuid] ?? 0, [owned]);

  const setOwned = useCallback(
    async (printingUuid: string, quantity: number) => {
      await collectionApi.setOwned({ printing: printingUuid, quantity });
      qc.invalidateQueries({ queryKey: ["owned-map"] });
      qc.invalidateQueries({ queryKey: ["collection"] });
      qc.invalidateQueries({ queryKey: ["collection-summary"] });
    },
    [qc],
  );

  return { owned: owned ?? {}, ownedOf, setOwned };
}
