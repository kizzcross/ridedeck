import { api } from "@/lib/api";
import type { MiniUser, Paginated } from "./types";
import type { CardListItem } from "./cards";

export interface Friendship {
  uuid: string;
  requester: MiniUser;
  addressee: MiniUser;
  status: "pending" | "accepted";
  direction: "incoming" | "outgoing" | "friend";
  created_at: string;
  responded_at: string | null;
}

export interface AvatarOption {
  key: string;
  label: string;
  nation: string;
}

export interface FavoriteCard {
  uuid: string;
  card: CardListItem;
  created_at: string;
}

export const socialApi = {
  // Friends
  async friends(): Promise<MiniUser[]> {
    const { data } = await api.get<MiniUser[]>("/friends/friends/");
    return data;
  },
  async requests(): Promise<{ incoming: Friendship[]; outgoing: Friendship[] }> {
    const { data } = await api.get("/friends/requests/");
    return data;
  },
  async addFriend(username: string): Promise<Friendship> {
    const { data } = await api.post<Friendship>("/friends/add/", { username });
    return data;
  },
  async acceptFriend(uuid: string): Promise<Friendship> {
    const { data } = await api.post<Friendship>(`/friends/${uuid}/accept/`);
    return data;
  },
  async removeFriend(uuid: string): Promise<void> {
    await api.delete(`/friends/${uuid}/`);
  },

  async promoteToAdmin(username: string, promote = true) {
    const { data } = await api.post<{ username: string; role: string; is_platform_admin: boolean }>(
      "/admin/users/promote/",
      { username, promote },
    );
    return data;
  },

  // Avatars
  async avatarOptions(): Promise<AvatarOption[]> {
    const { data } = await api.get<{ options: AvatarOption[] }>("/avatars/options/");
    return data.options;
  },

  // Favorites
  async favorites(): Promise<Paginated<FavoriteCard>> {
    const { data } = await api.get<Paginated<FavoriteCard>>("/me/favorites/");
    return data;
  },
  async favoriteIds(): Promise<string[]> {
    const { data } = await api.get<{ card_uuids: string[] }>("/me/favorites/ids/");
    return data.card_uuids;
  },
  async toggleFavorite(cardUuid: string): Promise<boolean> {
    const { data } = await api.post<{ favorited: boolean }>("/me/favorites/", { card: cardUuid });
    return data.favorited;
  },
};

export interface PublicProfile {
  uuid: string;
  username: string;
  role: string;
  date_joined: string;
  profile: {
    display_name: string;
    bio: string;
    avatar: string | null;
    avatar_key: string;
    country: string;
    favorite_nation: string;
  };
  friend_count: number;
  friendship_state: "self" | "none" | "friend" | "incoming" | "outgoing";
  friendship_uuid: string | null;
}

export const profileApi = {
  async publicProfile(username: string): Promise<PublicProfile> {
    const { data } = await api.get<PublicProfile>(`/users/${username}/`);
    return data;
  },
  async userFavoriteCards(username: string): Promise<FavoriteCard[]> {
    const { data } = await api.get<Paginated<FavoriteCard>>(`/users/${username}/favorite-cards/`, {
      params: { page_size: 60 },
    });
    return data.results;
  },
  async updateProfile(payload: Record<string, unknown>) {
    const { data } = await api.patch("/me/profile/", payload);
    return data;
  },
};
