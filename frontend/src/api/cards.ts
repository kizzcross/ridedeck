import { api } from "@/lib/api";
import type { Paginated } from "./types";

export interface CardPrintingLite {
  uuid: string;
  card_number: string;
  rarity: string;
  image_url: string;
  price: string | null;
}

export interface CardListItem {
  uuid: string;
  name: string;
  slug: string;
  grade: number;
  power: number | null;
  shield: number | null;
  critical: number;
  card_type: string;
  trigger: string;
  nation: string;
  clan: string;
  is_persona_ride: boolean;
  default_printing: CardPrintingLite | null;
}

export interface CardPrinting {
  uuid: string;
  card_number: string;
  set_code: string;
  set_name: string;
  rarity: string;
  language: string;
  illustrator: string;
  finish: string;
  image_url: string;
  price: string | null;
  release_date: string | null;
}

export interface CardDetail extends CardListItem {
  ability_text: string;
  flavor_text: string;
  race: string;
  keywords: string[];
  rules_data: Record<string, unknown>;
  equivalence_strategy: string;
  printings: CardPrinting[];
  format_legalities: { format_code: string; legality: string }[];
  external_ids: { source: string; identifier: string }[];
}

export interface CardSet {
  uuid: string;
  code: string;
  name: string;
  slug: string;
  release_date: string | null;
  card_count: number;
}

export interface CardFilters {
  search?: string;
  grade?: string;
  nation?: string;
  card_type?: string;
  trigger?: string;
  set_code?: string;
  is_trigger?: boolean;
  format_code?: string;
  page?: number;
  ordering?: string;
}

export const cardsApi = {
  async list(params: Record<string, string | number | boolean | undefined>) {
    const clean = Object.fromEntries(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== "" && v !== false),
    );
    const { data } = await api.get<Paginated<CardListItem>>("/cards/", { params: clean });
    return data;
  },
  async detail(slug: string) {
    const { data } = await api.get<CardDetail>(`/cards/${slug}/`);
    return data;
  },
  async sets() {
    const { data } = await api.get<Paginated<CardSet>>("/sets/", { params: { page_size: 100 } });
    return data.results;
  },
};
