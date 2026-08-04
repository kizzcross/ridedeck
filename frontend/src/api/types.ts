export type PlatformRole = "member" | "platform_admin";

export interface UserProfile {
  display_name: string;
  bio: string;
  avatar: string | null;
  avatar_key: string;
  country: string;
  favorite_nation: string;
  referral_code?: string;
}

export interface UserPreference {
  theme: "dark" | "light" | "system";
  default_format: string;
  show_collection_in_builder: boolean;
  locale: string;
}

export interface User {
  uuid: string;
  email: string;
  username: string;
  role: PlatformRole;
  is_platform_admin: boolean;
  email_verified: boolean;
  date_joined: string;
  profile: UserProfile;
  preference: UserPreference;
  friend_count: number;
}

export interface MiniUser {
  uuid: string;
  username: string;
  display_name: string;
  avatar_key: string;
  favorite_nation: string;
  role: PlatformRole;
  is_platform_admin: boolean;
}

export interface TokenPair {
  access: string;
  refresh: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
