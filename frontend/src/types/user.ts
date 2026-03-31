export interface User {
  id: string;
  email: string;
  role: "user" | "admin";
  daily_quota: number;
  today_usage: number;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}
