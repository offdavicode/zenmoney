'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Plus, PauseCircle, PlayCircle, Trash2, Edit2 } from 'lucide-react';
import { formatCurrency, formatCurrencyInput, parseCurrencyInput } from '@/utils/formatters';
import { listRecurrences, createRecurrence, updateRecurrence, pauseRecurrence, resumeRecurrence, deleteRecurrence, RecurrenceOut } from '@/services/recurrences.service';
import { useTransactions } from '@/contexts/TransactionsContext';
import { Modal } from '@/components/ui/Modal';

export function RecurrencesSection() {
  const { categories } = useTransactions();
  const [recurrences, setRecurrences] = useState<RecurrenceOut[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [msg, setMsg] = useState('');
  
  const [showForm, setShowForm] = useState(false);
  const [amountRaw, setAmountRaw] = useState('');
  const [description, setDescription] = useState('');
  const [categoryId, setCategoryId] = useState<number | ''>('');
  const [type, setType] = useState<'income' | 'expense'>('expense');
  const [dayOfMonth, setDayOfMonth] = useState<number | ''>('');
  const [startDate, setStartDate] = useState('');

  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editRecId, setEditRecId] = useState<number | null>(null);
  const [editAmountRaw, setEditAmountRaw] = useState('');
  const [editDescription, setEditDescription] = useState('');
  const [editCategoryId, setEditCategoryId] = useState<number | ''>('');
  const [editType, setEditType] = useState<'income' | 'expense'>('expense');
  const [editDayOfMonth, setEditDayOfMonth] = useState<number | ''>('');

  const handleOpenEdit = (rec: RecurrenceOut) => {
    setEditRecId(rec.id);
    setEditAmountRaw(formatCurrencyInput(rec.amount));
    setEditDescription(rec.description || '');
    setEditCategoryId(rec.category_id || '');
    setEditType(rec.type);
    setEditDayOfMonth(rec.day_of_month);
    setIsEditModalOpen(true);
  };

  const handleSaveEdit = async () => {
    if (!editRecId || !editDescription || !editAmountRaw || !editDayOfMonth) return;
    setIsLoading(true);
    try {
      await updateRecurrence(editRecId, {
        description: editDescription,
        amount: parseCurrencyInput(editAmountRaw),
        category_id: editCategoryId ? Number(editCategoryId) : null,
        type: editType,
        day_of_month: Number(editDayOfMonth)
      });
      setMsg('Recorrência atualizada!');
      setTimeout(() => setMsg(''), 3000);
      setIsEditModalOpen(false);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const loadData = async () => {
    try {
      const recData = await listRecurrences();
      setRecurrences(recData);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
    const now = new Date();
    setStartDate(now.toISOString().split('T')[0]);
  }, []);

  const handleOpenNew = () => {
    setAmountRaw('');
    setDescription('');
    setCategoryId('');
    setType('expense');
    setDayOfMonth('');
    setShowForm(true);
  };

  const handleSave = async () => {
    if (!description || !amountRaw || !dayOfMonth || !startDate) return;
    setIsLoading(true);
    try {
      await createRecurrence({
        description,
        amount: parseCurrencyInput(amountRaw),
        category_id: categoryId ? Number(categoryId) : null,
        type,
        day_of_month: Number(dayOfMonth),
        start_date: startDate,
        frequency: 'monthly'
      });
      setMsg('Recorrência criada!');
      setTimeout(() => setMsg(''), 3000);
      setShowForm(false);
      await loadData();
    } catch (e: any) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handlePauseResume = async (rec: RecurrenceOut) => {
    setIsLoading(true);
    try {
      if (rec.status === 'active') {
        await pauseRecurrence(rec.id);
      } else {
        await resumeRecurrence(rec.id);
      }
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Tem certeza que deseja excluir esta recorrência?')) return;
    setIsLoading(true);
    try {
      await deleteRecurrence(id);
      await loadData();
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Transações Recorrentes</h2>
          <p className="text-sm text-muted">Agendamentos automáticos</p>
        </div>
        <Button variant="outline" size="sm" className="gap-2" onClick={handleOpenNew}>
          <Plus size={16} /> Nova
        </Button>
      </div>

      {msg && <p className="text-sm text-[var(--accent-green)] mb-3">{msg}</p>}

      {showForm && (
        <div className="flex flex-col gap-3 mb-4 p-4 rounded-xl border border-border bg-surface-hover animate-fade-in">
          <h3 className="text-sm font-semibold">Nova Recorrência Mensal</h3>
          
          <Input 
            label="Descrição" 
            value={description} 
            onChange={e => setDescription(e.target.value)} 
            placeholder="Ex: Aluguel"
          />
          
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Valor (R$)</label>
              <input
                type="text"
                inputMode="numeric"
                value={amountRaw}
                onChange={(e) => setAmountRaw(formatCurrencyInput(parseCurrencyInput(e.target.value)))}
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                placeholder="0,00"
              />
            </div>
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Categoria</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={categoryId}
                onChange={e => setCategoryId(Number(e.target.value))}
              >
                <option value="" disabled>Selecione</option>
                {categories.filter(c => c.type === type).map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Tipo</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={type}
                onChange={e => {
                  setType(e.target.value as 'income' | 'expense');
                  setCategoryId('');
                }}
              >
                <option value="expense">Despesa</option>
                <option value="income">Receita</option>
              </select>
            </div>
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Dia do mês</label>
              <input
                type="number"
                min="1"
                max="31"
                value={dayOfMonth}
                onChange={(e) => setDayOfMonth(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                placeholder="1 a 31"
              />
            </div>
          </div>

          <div className="flex gap-2 mt-2">
            <Button size="sm" onClick={handleSave} isLoading={isLoading} disabled={!description || !amountRaw || !dayOfMonth}>
              Salvar
            </Button>
            <Button size="sm" variant="outline" onClick={() => setShowForm(false)}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {recurrences.length === 0 ? (
          <p className="text-sm text-muted">Nenhuma transação recorrente configurada.</p>
        ) : (
          recurrences.map((rec) => {
            const isPaused = rec.status === 'paused';
            return (
              <div key={rec.id} className={`flex items-center justify-between p-4 rounded-xl border border-border transition-colors ${isPaused ? 'bg-surface opacity-75' : 'bg-surface hover:border-[var(--accent-blue)]'}`}>
                <div className="flex items-center gap-3">
                  <div>
                    <p className={`text-sm font-semibold ${isPaused ? 'line-through text-muted' : ''}`}>{rec.description}</p>
                    <p className="text-xs text-muted">Todo dia {rec.day_of_month} • {formatCurrency(rec.amount)}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`hidden sm:inline-flex px-2 py-1 rounded-full text-xs font-medium ${isPaused ? 'bg-surface-hover text-muted' : 'bg-[var(--accent-green)]/10 text-[var(--accent-green)]'}`}>
                    {isPaused ? 'Pausado' : 'Ativo'}
                  </span>
                  <button onClick={() => handleOpenEdit(rec)} disabled={isLoading} className="p-2 text-muted hover:text-[var(--accent-blue)] transition-colors disabled:opacity-50" title="Editar">
                    <Edit2 size={18} />
                  </button>
                  <button onClick={() => handlePauseResume(rec)} disabled={isLoading} className="p-2 text-muted hover:text-[var(--accent-amber)] transition-colors disabled:opacity-50" title={isPaused ? "Retomar" : "Pausar"}>
                    {isPaused ? <PlayCircle size={18} /> : <PauseCircle size={18} />}
                  </button>
                  <button onClick={() => handleDelete(rec.id)} disabled={isLoading} className="p-2 text-muted hover:text-[var(--accent-red)] transition-colors disabled:opacity-50" title="Cancelar">
                    <Trash2 size={18} />
                  </button>
                </div>
              </div>
            );
          })
        )}
      </div>

      <Modal isOpen={isEditModalOpen} onClose={() => setIsEditModalOpen(false)} title="Editar Recorrência">
        <div className="flex flex-col gap-4">
          <Input 
            label="Descrição" 
            value={editDescription} 
            onChange={e => setEditDescription(e.target.value)} 
            placeholder="Ex: Aluguel"
          />
          
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Valor (R$)</label>
              <input
                type="text"
                inputMode="numeric"
                value={editAmountRaw}
                onChange={(e) => setEditAmountRaw(formatCurrencyInput(parseCurrencyInput(e.target.value)))}
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                placeholder="0,00"
              />
            </div>
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Categoria</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={editCategoryId}
                onChange={e => setEditCategoryId(e.target.value ? Number(e.target.value) : '')}
              >
                <option value="">Selecione</option>
                {categories.filter(c => c.type === editType).map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-3">
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Tipo</label>
              <select 
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                value={editType}
                onChange={e => {
                  setEditType(e.target.value as 'income' | 'expense');
                  setEditCategoryId('');
                }}
              >
                <option value="expense">Despesa</option>
                <option value="income">Receita</option>
              </select>
            </div>
            <div className="flex-1 w-full">
              <label className="text-sm font-medium text-foreground block mb-1">Dia do mês</label>
              <input
                type="number"
                min="1"
                max="31"
                value={editDayOfMonth}
                onChange={(e) => setEditDayOfMonth(Number(e.target.value))}
                className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                placeholder="1 a 31"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 mt-4">
            <Button size="sm" variant="outline" onClick={() => setIsEditModalOpen(false)}>
              Cancelar
            </Button>
            <Button size="sm" onClick={handleSaveEdit} isLoading={isLoading} disabled={!editDescription || !editAmountRaw || !editDayOfMonth}>
              Salvar
            </Button>
          </div>
        </div>
      </Modal>
    </Card>
  );
}
