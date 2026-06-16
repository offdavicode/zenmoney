import { apiGet, apiPost, apiPut, apiDelete } from './api';



export interface TransactionCreate {
  category_id: number | null;
  type: 'income' | 'expense';
  amount: number;
  date: string; 
  description?: string | null;
  emotion?: string;
}

export interface TransactionUpdate {
  category_id?: number | null;
  type?: 'income' | 'expense';
  amount?: number;
  date?: string;
  description?: string | null;
  emotion?: string;
}

export interface TransactionOut {
  id: number;
  user_id: number;
  category_id: number | null;
  recurrence_id: number | null;
  is_recurring: boolean;
  type: 'income' | 'expense';
  amount: number;
  date: string;
  registered_at: string;
  description: string | null;
  emotion: string;
}

export interface EmotionOption {
  value: string;
  label: string;
}

export interface TransactionFilters {
  month?: string;
  type?: string;
  category?: string;
  emotion?: string;
  start_date?: string;
  end_date?: string;
}



export async function createTransaction(data: TransactionCreate): Promise<TransactionOut> {
  const tx = await apiPost<TransactionOut>('/transactions/', data);
  return { ...tx, amount: Number(tx.amount) };
}

export async function listTransactions(filters?: TransactionFilters): Promise<TransactionOut[]> {
  const params = new URLSearchParams();
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
  }
  const query = params.toString();
  const txs = await apiGet<TransactionOut[]>(`/transactions/${query ? `?${query}` : ''}`);
  return txs.map(tx => ({ ...tx, amount: Number(tx.amount) }));
}

export async function getTransaction(id: number): Promise<TransactionOut> {
  const tx = await apiGet<TransactionOut>(`/transactions/${id}`);
  return { ...tx, amount: Number(tx.amount) };
}

export async function updateTransaction(id: number, data: TransactionUpdate): Promise<TransactionOut> {
  const tx = await apiPut<TransactionOut>(`/transactions/${id}`, data);
  return { ...tx, amount: Number(tx.amount) };
}

export async function deleteTransaction(id: number): Promise<void> {
  return apiDelete(`/transactions/${id}`);
}

export async function listEmotions(): Promise<EmotionOption[]> {
  return apiGet<EmotionOption[]>('/transactions/emotions');
}
