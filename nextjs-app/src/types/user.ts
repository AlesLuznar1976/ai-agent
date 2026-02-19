export interface User {
  id: number;
  username: string;
  role: string;
  permissions: string[];
  mailbox?: string;
}

export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
}
