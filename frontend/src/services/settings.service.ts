import { apiGet, apiPut, apiDelete } from './api';



export interface ProfileUpdate {
  name?: string;
  email?: string;
}

export interface PasswordUpdate {
  current_password: string;
  new_password: string;
}

export interface AccountDeleteRequest {
  current_password: string;
}

export interface BudgetLimitStatus {
  category_id: number | null;
  category_name: string;
  limit_amount: number;
  spent_amount: number;
  remaining_amount: number;
  usage_percentage: number;
  is_exceeded: boolean;
}

export interface BudgetOut {
  month: string;
  global_limit: BudgetLimitStatus | null;
  category_limits: BudgetLimitStatus[];
  alerts_enabled: boolean;
}

export interface CategoryLimitInput {
  category_id: number;
  amount: number | null;
}

export interface BudgetUpdate {
  global_limit?: number | null;
  category_limits?: CategoryLimitInput[];
}

export interface BudgetAlertResponse {
  month: string;
  alert: {
    month: string;
    scope: string;
    category_id: number | null;
    category_name: string;
    threshold_percent: number;
    limit_amount: number;
    spent_amount: number;
    usage_percentage: number;
    message: string;
  } | null;
}

export interface SurvivalModeConfig {
  activation_percentage: number;
  is_default: boolean;
}

export interface SurvivalModeConfigUpdate {
  activation_percentage: number;
}

export interface UserOut {
  id: number;
  name: string;
  email: string;
}



export async function getProfile(): Promise<UserOut> {
  return apiGet<UserOut>('/settings/profile');
}

export async function updateProfile(data: ProfileUpdate): Promise<UserOut> {
  return apiPut<UserOut>('/settings/profile', data);
}

export async function updatePassword(data: PasswordUpdate): Promise<{ message: string }> {
  return apiPut<{ message: string }>('/settings/password', data);
}

export async function deleteAccount(data: AccountDeleteRequest): Promise<{ message: string }> {
  return apiDelete<{ message: string }>('/settings/account', data);
}

export async function getBudget(month?: string): Promise<BudgetOut> {
  const query = month ? `?month=${month}` : '';
  return apiGet<BudgetOut>(`/settings/budget${query}`);
}

export async function updateBudget(data: BudgetUpdate, month?: string): Promise<BudgetOut> {
  const query = month ? `?month=${month}` : '';
  return apiPut<BudgetOut>(`/settings/budget${query}`, data);
}

export async function getBudgetAlert(month?: string): Promise<BudgetAlertResponse> {
  const query = month ? `?month=${month}` : '';
  return apiGet<BudgetAlertResponse>(`/settings/budget/alert${query}`);
}

export async function getSurvivalModeConfig(): Promise<SurvivalModeConfig> {
  return apiGet<SurvivalModeConfig>('/settings/survival-mode');
}

export async function updateSurvivalModeConfig(data: SurvivalModeConfigUpdate): Promise<SurvivalModeConfig> {
  return apiPut<SurvivalModeConfig>('/settings/survival-mode', data);
}
