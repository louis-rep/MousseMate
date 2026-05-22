export interface UserRead {
  id: number;
  username: string;
  created_at: string;
}

export interface Token {
  access_token: string;
  token_type: string;
}
