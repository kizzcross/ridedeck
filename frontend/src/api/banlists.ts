import { api } from "@/lib/api";
import type { Paginated } from "./types";

export interface MiniCard {
  uuid: string;
  name: string;
  grade: number;
  nation: string;
  clan: string;
  image: string;
}

export interface GroupMember {
  uuid: string;
  card: MiniCard;
  per_card_limit: number | null;
}
export interface RestrictionGroup {
  uuid: string;
  name: string;
  kind: "choice" | "max_distinct" | "max_total";
  limit_value: number;
  note: string;
  members: GroupMember[];
}
export interface BanlistEntry {
  uuid: string;
  restriction_type: string;
  card: MiniCard | null;
  group: RestrictionGroup | null;
  limit_value: number | null;
  effective_limit: number;
  note: string;
}
export interface BanlistVersion {
  uuid: string;
  version: number;
  status: string;
  effective_date: string | null;
  notes: string;
  source: string;
  entries: BanlistEntry[];
}
export interface BanlistListItem {
  uuid: string;
  name: string;
  category: "official" | "community" | "tournament_custom";
  is_official: boolean;
  format_code: string;
  objective: string;
  owner: { username: string; uuid: string } | null;
  like_count: number;
  favorite_count: number;
  entry_count: number;
  updated_at: string;
}
export interface BanlistDetail extends BanlistListItem {
  description: string;
  source: string;
  is_public: boolean;
  is_listed: boolean;
  current_version: BanlistVersion;
  is_owner: boolean;
}

export const banlistsApi = {
  async list(params: Record<string, string | number | undefined> = {}) {
    const { data } = await api.get<Paginated<BanlistListItem>>("/banlists/", {
      params: { page_size: 40, ...params },
    });
    return data;
  },
  async detail(uuid: string) {
    const { data } = await api.get<BanlistDetail>(`/banlists/${uuid}/`);
    return data;
  },
  async create(payload: { name: string; format_code: string; objective?: string }) {
    const { data } = await api.post<BanlistDetail>("/banlists/", payload);
    return data;
  },
  async update(
    uuid: string,
    payload: Partial<{ name: string; format_code: string; objective: string; description: string; is_public: boolean; is_listed: boolean }>,
  ) {
    const { data } = await api.patch<BanlistDetail>(`/banlists/${uuid}/`, payload);
    return data;
  },
  async addEntry(uuid: string, entry: { restriction_type: string; card?: string; group?: string; limit_value?: number }) {
    const { data } = await api.post<BanlistVersion>(`/banlists/${uuid}/entry/`, entry);
    return data;
  },
  async addGroup(uuid: string, group: { name: string; kind: string; limit_value: number; members: string[] }) {
    const { data } = await api.post<BanlistVersion>(`/banlists/${uuid}/group/`, group);
    return data;
  },
  async removeGroup(uuid: string, groupUuid: string) {
    const { data } = await api.delete<BanlistVersion>(`/banlists/${uuid}/group/`, { data: { group: groupUuid } });
    return data;
  },
  async fork(uuid: string) {
    const { data } = await api.post<BanlistDetail>(`/banlists/${uuid}/fork/`);
    return data;
  },
  async remove(uuid: string) {
    await api.delete(`/banlists/${uuid}/`);
  },
  async makeOfficial(uuid: string, official = true) {
    const { data } = await api.post<{ is_official: boolean }>(`/banlists/${uuid}/make-official/`, { official });
    return data;
  },
  async restrictionMap(uuid: string) {
    const { data } = await api.get<{ format_code: string; restrictions: Record<string, RestrictionInfo> }>(
      `/banlists/${uuid}/restriction-map/`,
    );
    return data.restrictions;
  },
};

export interface RestrictionInfo {
  type: string;
  limit: number;
  group?: string;
  group_kind?: string;
}
