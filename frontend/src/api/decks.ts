import { api } from "@/lib/api";
import type { Paginated } from "./types";
import type { CardListItem } from "./cards";

export type Zone = "main_deck" | "ride_deck" | "g_deck";
export type Visibility = "private" | "unlisted" | "public";

export interface DeckEntry {
  uuid: string;
  card: CardListItem;
  zone: Zone;
  quantity: number;
  preferred_printing: string | null;
}

export interface DeckVersion {
  uuid: string;
  version_number: number;
  notes: string;
  entries: DeckEntry[];
  zone_counts: Record<Zone, number>;
}

export interface DeckOwner {
  username: string;
  uuid: string;
  avatar_key: string;
}

export interface DeckListItem {
  uuid: string;
  title: string;
  format_code: string;
  visibility: Visibility;
  owner: DeckOwner;
  nation_focus: string;
  clan_focus: string;
  archetype: string;
  like_count: number;
  favorite_count: number;
  power_stars: number | null;
  cover_image: string | null;
  main_count: number;
  updated_at: string;
}

export interface DeckDetail {
  uuid: string;
  title: string;
  description: string;
  format_code: string;
  visibility: Visibility;
  owner: DeckOwner;
  nation_focus: string;
  clan_focus: string;
  archetype: string;
  tags: string[];
  guide: string;
  combos: string;
  matchups: string;
  side_notes: string;
  changelog: string;
  like_count: number;
  favorite_count: number;
  power_stars: number | null;
  forked_from: number | null;
  current_version: DeckVersion;
  is_owner: boolean;
  created_at: string;
  updated_at: string;
}

export interface ValidationResult {
  is_valid: boolean;
  basic?: boolean;
  errors: { code: string; message: string; zone?: string; card_id?: string }[];
  warnings: { code: string; message: string; card_id?: string }[];
  summary: Record<string, number>;
}

export interface ImportCard {
  uuid: string;
  name: string;
  grade: number;
  default_printing?: { image_url?: string | null } | null;
}
export type ImportConfidence = "exact" | "code" | "fuzzy" | "ambiguous" | "unmatched";
export interface ImportLine {
  raw: string;
  input_name: string;
  quantity: number;
  zone: Zone;
  confidence: ImportConfidence;
  score: number;
  card: ImportCard | null;
  suggestions: ImportCard[];
}

export const decksApi = {
  async importPreview(text: string, default_zone: Zone = "main_deck") {
    const { data } = await api.post<{ lines: ImportLine[] }>("/decks/import-preview/", { text, default_zone });
    return data.lines;
  },
  async importApply(uuid: string, lines: { card: string; zone: Zone; quantity: number }[], replace: boolean) {
    const { data } = await api.post<DeckVersion>(`/decks/${uuid}/import-list/`, { lines, replace });
    return data;
  },
  async myDecks() {
    const { data } = await api.get<Paginated<DeckListItem>>("/decks/", { params: { mine: 1, page_size: 60 } });
    return data;
  },
  async publicDecks(params: Record<string, string | number | undefined> = {}) {
    const { data } = await api.get<Paginated<DeckListItem>>("/decks/", { params });
    return data;
  },
  async detail(uuid: string) {
    const { data } = await api.get<DeckDetail>(`/decks/${uuid}/`);
    return data;
  },
  async create(payload: { title: string; format_code: string; visibility?: Visibility }) {
    const { data } = await api.post<DeckDetail>("/decks/", payload);
    return data;
  },
  async update(uuid: string, payload: Partial<DeckDetail>) {
    const { data } = await api.patch<DeckDetail>(`/decks/${uuid}/`, payload);
    return data;
  },
  async remove(uuid: string) {
    await api.delete(`/decks/${uuid}/`);
  },
  async setEntry(uuid: string, entry: { card: string; zone: Zone; quantity: number; preferred_printing?: string }) {
    const { data } = await api.post<DeckVersion>(`/decks/${uuid}/entry/`, entry);
    return data;
  },
  async validate(uuid: string) {
    const { data } = await api.get<ValidationResult>(`/decks/${uuid}/validate/`);
    return data;
  },
  async publish(uuid: string, visibility: Visibility) {
    const { data } = await api.post<{ visibility: Visibility }>(`/decks/${uuid}/publish/`, { visibility });
    return data;
  },
  async fork(uuid: string) {
    const { data } = await api.post<DeckDetail>(`/decks/${uuid}/fork/`);
    return data;
  },
};
