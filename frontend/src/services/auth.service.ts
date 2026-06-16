import { apiPost, apiGet, setToken, clearToken } from './api';



export interface UserOut {
  id: number;
  name: string;
  email: string;
}

export interface TokenOut {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserOut;
}



export async function registerUser(payload: {
  name: string;
  email: string;
  password: string;
}): Promise<UserOut> {
  return apiPost<UserOut>('/auth/register', payload);
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenOut> {
  const data = await apiPost<TokenOut>('/auth/login', payload);
  setToken(data.access_token);
  return data;
}

export async function logoutUser(): Promise<void> {
  try {
    await apiPost('/auth/logout');
  } finally {
    clearToken();
  }
}

export async function getCurrentUser(): Promise<UserOut> {
  return apiGet<UserOut>('/auth/me');
}
