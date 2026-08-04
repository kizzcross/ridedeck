import { api } from "@/lib/api";
import type { Paginated } from "./types";
import type { CardListItem, CardPrinting } from "./cards";

export interface CollectionPrinting {
  uuid: string;
  printing: CardPrinting;
  quantity: number;
  language: string;
  condition: string;
  finish: string;
  note: string;
  price_paid: string | null;
}

export interface CollectionItem {
  uuid: string;
  card: CardListItem;
  note: string;
  owned_quantity: number;
  printings: CollectionPrinting[];
}

export interface CollectionReport {
  summary: {
    used: number;
    owned: number;
    missing: number;
    owned_pct: number;
    missing_cost_estimate: string | null;
  };
  shopping_list: {
    card_uuid: string;
    card_name: string;
    zone: string;
    used: number;
    owned: number;
    missing: number;
    unit_price: string | null;
    line_cost: string | null;
  }[];
}

export const collectionApi = {
  async list(search = "") {
    const { data } = await api.get<Paginated<CollectionItem>>("/collection/", {
      params: { search: search || undefined, page_size: 60 },
    });
    return data;
  },
  async setOwned(payload: { printing: string; quantity: number; condition?: string; language?: string; finish?: string }) {
    const { data } = await api.post<{ ok: boolean; card_uuid: string; owned: number }>("/collection/set/", payload);
    return data;
  },
  async ownedMap() {
    const { data } = await api.get<{ owned: Record<string, number> }>("/collection/owned-map/");
    return data.owned;
  },
  async summary() {
    const { data } = await api.get<{ distinct_cards: number; total_cards: number }>("/collection/summary/");
    return data;
  },
  async deckReport(deckUuid: string) {
    const { data } = await api.get<CollectionReport>(`/decks/${deckUuid}/collection-report/`);
    return data;
  },
};
