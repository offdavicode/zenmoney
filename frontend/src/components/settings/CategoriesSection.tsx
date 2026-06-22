'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Plus, Edit2, Trash2 } from 'lucide-react';
import { createCategory, updateCategory, deleteCategory, CategoryOut } from '@/services/categories.service';
import { useTransactions } from '@/contexts/TransactionsContext';

export function CategoriesSection() {
  const { categories, refreshTransactions } = useTransactions();
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');
  
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<number | null>(null);
  const [name, setName] = useState('');
  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [isEssential, setIsEssential] = useState(false);

  const handleOpenNew = () => {
    setEditId(null);
    setName('');
    setType('expense');
    setIsEssential(false);
    setShowForm(true);
  };

  const handleOpenEdit = (cat: CategoryOut) => {
    setEditId(cat.id);
    setName(cat.name);
    setType(cat.type);
    setIsEssential(cat.is_essential);
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!name) return;
    setIsLoading(true);
    try {
      if (editId) {
        await updateCategory(editId, { name, is_essential: isEssential });
        setMsg('Categoria atualizada!');
      } else {
        await createCategory({ name, type, is_essential: isEssential });
        setMsg('Categoria criada!');
      }
      setTimeout(() => setMsg(''), 3000);
      setShowForm(false);
      await refreshTransactions();
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja excluir esta categoria?')) return;
    setIsLoading(true);
    try {
      await deleteCategory(id);
      await refreshTransactions();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const customCategories = categories.filter(c => !c.is_default);

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Categorias Personalizadas</h2>
          <p className="text-sm text-muted">Gerencie suas próprias categorias</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={handleOpenNew}>
          <Plus size={16} /> Nova
        </Button>
      </div>

      {msg && <p className="text-sm text-[var(--accent-green)] mb-3">{msg}</p>}

      {showForm && (
        <div className="flex flex-col gap-3 mb-4 p-4 rounded-xl border border-border bg-surface-hover animate-fade-in">
          <h3 className="text-sm font-semibold">{editId ? 'Editar Categoria' : 'Nova Categoria'}</h3>
          
          <Input 
            label="Nome" 
            value={name} 
            onChange={e => setName(e.target.value)} 
            placeholder="Ex: Assinaturas"
          />
          
          {!editId && (
            <div className="flex flex-col gap-1">
              <label className="text-sm font-medium text-foreground">Tipo</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={type}
                onChange={e => setType(e.target.value as 'income' | 'expense')}
              >
                <option value="expense">Despesa</option>
                <option value="income">Receita</option>
              </select>
            </div>
          )}

          <div className="flex items-center gap-2 mt-1">
            <input 
              type="checkbox" 
              id="isEssential" 
              checked={isEssential} 
              onChange={e => setIsEssential(e.target.checked)} 
              className="rounded border-border text-primary focus:ring-primary h-4 w-4"
            />
            <label htmlFor="isEssential" className="text-sm text-foreground">Categoria Essencial (Sobrevivência)</label>
          </div>

          <div className="flex gap-2 mt-2">
            <Button size="sm" onClick={handleSave} isLoading={isLoading} disabled={!name}>
              Salvar
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowForm(false)}>
              Cancelar
            </Button>
          </div>
        </div>
      )}
      
      <div className="flex flex-col gap-2">
        {customCategories.length === 0 ? (
          <p className="text-sm text-muted">Nenhuma categoria personalizada criada.</p>
        ) : (
          customCategories.map(cat => (
            <div key={cat.id} className="flex items-center justify-between p-3 rounded-lg border border-border">
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium">{cat.name}</span>
                {cat.is_essential && (
                  <span className="ml-2 text-xs text-brand-600 bg-brand-50 px-2 py-0.5 rounded-full">Essencial</span>
                )}
              </div>
              <div className="flex gap-2">
                <button 
                  onClick={() => handleOpenEdit(cat)}
                  className="p-1.5 text-muted hover:text-foreground rounded bg-surface-hover"
                >
                  <Edit2 size={14} />
                </button>
                <button 
                  onClick={() => handleDelete(cat.id)}
                  disabled={isLoading}
                  className="p-1.5 text-muted hover:text-[var(--accent-red)] rounded bg-surface-hover disabled:opacity-50"
                >
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </Card>
  );
}
