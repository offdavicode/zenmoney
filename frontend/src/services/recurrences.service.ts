import { apiGet, apiPost, apiPut, apiPatch, apiDelete } from './api';
import { type TransactionOut } from './transactions.service';



export interface RecurrenceCreate {
  category_id: number | null;
  type: 'income' | 'expense';
  amount: number;
  description?: string | null;
  emotion?: string;
  frequency: 'monthly';
  day_of_month: number;
  start_date: string;
  end_date?: string | null;
}

export interface RecurrenceUpdate {
  category_id?: number | null;
  type?: 'income' | 'expense';
  amount?: number;
  description?: string | null;
  emotion?: string;
  frequency?: 'monthly';
  day_of_month?: number;
  start_date?: string;
  end_date?: string | null;
}

export interface RecurrenceOut {
  id: number;
  user_id: number;
  category_id: number | null;
  type: 'income' | 'expense';
  amount: number;
  description: string | null;
  emotion: string;
  frequency: 'monthly';
  day_of_month: number;
  start_date: string;
  end_date: string | null;
  next_run_date: string;
  is_active: boolean;
  status: 'active' | 'paused' | 'completed';
}

export interface RecurrenceRunDueResponse {
  through_date: string;
  generated_count: number;
  generated_transactions: TransactionOut[];
}



export async function createRecurrence(data: RecurrenceCreate): Promise<RecurrenceOut> {
  return apiPost<RecurrenceOut>('/recurrences/', data);
}

export async function listRecurrences(): Promise<RecurrenceOut[]> {
  return apiGet<RecurrenceOut[]>('/recurrences/');
}

export async function getRecurrence(id: number): Promise<RecurrenceOut> {
  return apiGet<RecurrenceOut>(`/recurrences/${id}`);
}

export async function updateRecurrence(id: number, data: RecurrenceUpdate): Promise<RecurrenceOut> {
  return apiPut<RecurrenceOut>(`/recurrences/${id}`, data);
}

export async function pauseRecurrence(id: number): Promise<RecurrenceOut> {
  return apiPatch<RecurrenceOut>(`/recurrences/${id}/pause`);
}

export async function resumeRecurrence(id: number): Promise<RecurrenceOut> {
  return apiPatch<RecurrenceOut>(`/recurrences/${id}/resume`);
}

export async function deleteRecurrence(id: number): Promise<void> {
  return apiDelete(`/recurrences/${id}`);
}

export async function runDueRecurrences(through_date?: string): Promise<RecurrenceRunDueResponse> {
  const payload = through_date ? { through_date } : undefined;
  return apiPost<RecurrenceRunDueResponse>('/recurrences/run-due', payload);
}
