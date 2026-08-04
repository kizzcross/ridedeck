import type { Zone } from "@/api/decks";

export const ZONES: { key: Zone; label: string }[] = [
  { key: "main_deck", label: "Main Deck" },
  { key: "ride_deck", label: "Ride Deck" },
  { key: "g_deck", label: "G Deck" },
];

export const ZONE_LABEL: Record<Zone, string> = {
  main_deck: "Main Deck",
  ride_deck: "Ride Deck",
  g_deck: "G Deck",
};

/** Grade 4 → G Deck by default, everything else → Main Deck (a sensible default;
 *  users can drag between zones). */
export function defaultZoneForGrade(grade: number): Zone {
  return grade === 4 ? "g_deck" : "main_deck";
}
