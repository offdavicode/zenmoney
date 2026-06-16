import { apiGet, apiPost, apiPut, apiDelete } from './api';



export interface CategoryCreate {
  name: string;
  type: 'income' | 'expense';
  parent_id?: number | null;
  is_essential?: boolean;
}

export interface CategoryUpdate {
  name?: string;
  parent_id?: number | null;
  is_essential?: boolean;
}

export interface CategoryOut {
  id: number;
  name: string;
  type: 'income' | 'expense';
  is_default: boolean;
  is_essential: boolean;
  parent_id: number | null;
}



export async function createCategory(data: CategoryCreate): Promise<CategoryOut> {
  return apiPost<CategoryOut>('/categories/', data);
}

export async function listCategories(): Promise<CategoryOut[]> {
  return apiGet<CategoryOut[]>('/categories/');
}

export async function updateCategory(id: number, data: CategoryUpdate): Promise<CategoryOut> {
  return apiPut<CategoryOut>(`/categories/${id}`, data);
}

export async function deleteCategory(id: number): Promise<void> {
  return apiDelete(`/categories/${id}`);
}
