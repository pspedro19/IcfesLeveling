export interface User {
  id: string;
  username: string;
  email: string;
  display_name: string;
  level: number;
  experience: number;
  rank: string;
  hp: number;
  mp: number;
  power: number;
  wisdom: number;
  speed: number;
  orbs: number;
  crystals: number;
  is_active: boolean;
  isAdmin?: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
}

export interface UserResponse extends User {
  // Additional fields from API response if needed
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: UserResponse;
}

export interface HeroClass {
  id: string;
  name: string;
  description: string;
  avatar_url?: string;
  stats_boost: Record<string, number>;
  special_ability: string;
  element: string;
}

export interface UserProfile {
  id: string;
  user_id: string;
  hero_class_id: string;
  hero_class?: HeroClass;
  personality_answers?: Record<string, any>;
  avatar_customization?: Record<string, any>;
}