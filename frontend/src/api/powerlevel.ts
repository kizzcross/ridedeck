import { api } from "@/lib/api";
import type { Paginated } from "./types";

export interface AdminCardRow {
  uuid: string;
  name: string;
  grade: number;
  nation: string;
  clan: string;
  image: string;
  power_value: number | null;
  power_status: "draft" | "published" | null;
}

export interface PowerHistoryEntry {
  previous_value: number | null;
  new_value: number | null;
  admin: string | null;
  justification: string;
  source: string;
  version: number;
  created_at: string;
}

export interface DeckPowerStats {
  has_data: boolean;
  unrated_cards?: number;
  format_code?: string;
  max_power_level?: number;
  simple_average?: number;
  weighted_average?: number;
  weighted_sum?: number;
  distribution?: Record<string, number>;
  count_at_or_above?: Record<string, number>;
  top_contributors?: { card_uuid: string; name: string; value: number; quantity: number }[];
  editorial_note?: string;
}

export const powerApi = {
  async scale() {
    const { data } = await api.get<{ min_value: number; max_value: number; descriptions: Record<string, string> }>(
      "/power-levels/scale/",
    );
    return data;
  },
  async adminCards(params: { format_code: string; search?: string; unrated?: string; page?: number }) {
    const { data } = await api.get<Paginated<AdminCardRow>>("/admin/power-levels/cards/", {
      params: { page_size: 40, ...params },
    });
    return data;
  },
  async setLevel(payload: { card: string; format_code: string; value: number; justification: string; status?: string }) {
    const { data } = await api.post("/admin/power-levels/set/", payload);
    return data;
  },
  async bulkSet(payload: { cards: string[]; format_code: string; value: number; justification: string }) {
    const { data } = await api.post<{ updated: number }>("/admin/power-levels/bulk/", payload);
    return data;
  },
  async history(card: string, format_code: string) {
    const { data } = await api.get<PowerHistoryEntry[]>("/admin/power-levels/history/", {
      params: { card, format_code },
    });
    return data;
  },
  async deckPower(deckUuid: string) {
    const { data } = await api.get<DeckPowerStats>(`/decks/${deckUuid}/power/`);
    return data;
  },
};
