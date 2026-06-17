'use client';

import { useState, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Select } from '@/components/ui/Select';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrencyInput, parseCurrencyInput, todayISO } from '@/utils/formatters';
import { useTransactions } from '@/contexts/TransactionsContext';
import { type TransactionCreate, type TransactionOut } from '@/services/transactions.service';
import { type RecurrenceCreate } from '@/services/recurrences.service';
import { Repeat, AlertTriangle } from 'lucide-react';
import { getSurvivalModeReport } from '@/services/reports.service';

interface TransactionFormProps {
  initialDate?: string;
  initialEmotionId?: string;
  initialTransaction?: TransactionOut;
  onSubmit: (transaction: TransactionCreate, id?: number) => void;
  onSubmitRecurrence?: (recurrence: RecurrenceCreate) => void;
  onCancel: () => void;
}

export function TransactionForm({ initialDate, initialEmotionId, initialTransaction, onSubmit, onSubmitRecurrence, onCancel }: TransactionFormProps) {
  const [type, setType] = useState<'expense' | 'income'>(initialTransaction?.type || 'expense');
  const [rawValue, setRawValue] = useState(initialTransaction ? formatCurrencyInput(initialTransaction.amount) : '');
  const [numericValue, setNumericValue] = useState(initialTransaction?.amount || 0);
  const [date, setDate] = useState(initialTransaction?.date || initialDate || todayISO());
  const [description, setDescription] = useState(initialTransaction?.description || '');
  const [categoryId, setCategoryId] = useState<number | ''>(initialTransaction?.category_id || '');
  const [emotionId, setEmotionId] = useState(initialTransaction?.emotion || initialEmotionId || '');
  const [isLoading, setIsLoading] = useState(false);
  const { categories } = useTransactions();

  
  const isEditing = !!initialTransaction;
  const [isRecurring, setIsRecurring] = useState(false);
  const [dayOfMonth, setDayOfMonth] = useState(() => {
    const d = initialDate || todayISO();
    return parseInt(d.split('-')[2], 10);
  });
  const [endDate, setEndDate] = useState('');
  const [blockedCategories, setBlockedCategories] = useState<number[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function loadSurvivalReport() {
      try {
        const monthStr = date.substring(0, 7);
        if (/^\d{4}-\d{2}$/.test(monthStr)) {
          const report = await getSurvivalModeReport({ month: monthStr });
          if (isMounted && report && report.is_active && report.recommendations) {
            const blocked = report.recommendations
              .filter(rec => rec.suggest_block_new_transactions)
              .map(rec => rec.category_id);
            setBlockedCategories(blocked);
          } else if (isMounted) {
            setBlockedCategories([]);
          }
        }
      } catch (e) {
        console.error('Erro ao verificar categorias bloqueadas no formulário:', e);
      }
    }
    loadSurvivalReport();
    return () => {
      isMounted = false;
    };
  }, [date]);

  const filteredCategories = categories.filter(c => c.type === type);

  
  const handleValueChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const input = e.target.value;
    const parsed = parseCurrencyInput(input);
    setNumericValue(parsed);
    setRawValue(formatCurrencyInput(parsed));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (numericValue <= 0) return;
    if (!emotionId) {
      alert('Por favor, selecione uma emoção.');
      return;
    }

    setIsLoading(true);
    await new Promise((r) => setTimeout(r, 400));

    if (isRecurring && !isEditing && onSubmitRecurrence) {
      const recurrence: RecurrenceCreate = {
        type,
        amount: numericValue,
        description: description.slice(0, 256) || undefined,
        category_id: categoryId === '' ? null : Number(categoryId),
        emotion: emotionId,
        frequency: 'monthly',
        day_of_month: dayOfMonth,
        start_date: date,
        end_date: endDate || undefined,
      };
      onSubmitRecurrence(recurrence);
    } else {
      const transaction: TransactionCreate = {
        type,
        amount: numericValue,
        date,
        description: description.slice(0, 256),
        category_id: categoryId === '' ? null : Number(categoryId),
        emotion: emotionId,
      };
      onSubmit(transaction, initialTransaction?.id);
    }
    setIsLoading(false);
  };

  
  const handleDateChange = (newDate: string) => {
    setDate(newDate);
    if (!isEditing && newDate) {
      const day = parseInt(newDate.split('-')[2], 10);
      if (!isNaN(day)) setDayOfMonth(day);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-5">
      
      {isEditing && initialTransaction?.is_recurring && (
        <div className="flex items-center gap-2 rounded-lg bg-[var(--accent-blue)]/10 border border-[var(--accent-blue)]/20 px-3 py-2.5 text-sm text-[var(--accent-blue)]">
          <Repeat size={14} />
          <span>Transação recorrente — editando apenas esta ocorrência.</span>
        </div>
      )}

      
      <div className="flex rounded-xl border border-border p-1 gap-1">
        <button
          type="button"
          onClick={() => { setType('expense'); setCategoryId(''); }}
          className={`flex-1 rounded-lg py-2.5 text-sm font-medium transition-all duration-200 ${type === 'expense'
              ? 'bg-brand-500 text-white shadow-sm'
              : 'text-muted hover:text-foreground'
            }`}
        >
          Despesa
        </button>
        <button
          type="button"
          onClick={() => { setType('income'); setCategoryId(''); }}
          className={`flex-1 rounded-lg py-2.5 text-sm font-medium transition-all duration-200 ${type === 'income'
              ? 'bg-brand-500 text-white shadow-sm'
              : 'text-muted hover:text-foreground'
            }`}
        >
          Receita
        </button>
      </div>

      
      <div className="flex w-full flex-col gap-1.5">
        <label className="text-sm font-medium text-foreground">Valor</label>
        <div className="relative">
          <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-muted">
            R$
          </span>
          <input
            type="text"
            inputMode="numeric"
            placeholder="0,00"
            value={rawValue}
            onChange={handleValueChange}
            required
            className="flex h-12 w-full rounded-md border border-border bg-surface pl-10 pr-3 py-2 text-lg font-semibold text-foreground transition-colors placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
          />
        </div>
      </div>

      
      <Input
        label="Data"
        type="date"
        value={date}
        onChange={(e) => handleDateChange(e.target.value)}
        required
      />

      
      <div className="flex w-full flex-col gap-1.5">
        <label className="text-sm font-medium text-foreground">
          Descrição <span className="text-muted font-normal">(opcional, máx. 256 caracteres)</span>
        </label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          maxLength={256}
          rows={2}
          placeholder="Ex: Compras do mês no supermercado"
          className="flex w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors placeholder:text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary resize-none"
        />
        <span className="text-xs text-muted text-right">{description.length}/256</span>
      </div>

      
      <Select
        label="Categoria"
        placeholder="Selecione uma categoria"
        value={categoryId.toString()}
        onChange={(e) => setCategoryId(Number(e.target.value))}
        required
        options={filteredCategories.map((c) => ({ value: c.id.toString(), label: c.name }))}
      />

      {categoryId !== '' && blockedCategories.includes(Number(categoryId)) && (
        <div className="flex items-start gap-2 p-3 text-xs text-[var(--accent-amber)] bg-[var(--accent-amber)]/10 border border-[var(--accent-amber)]/20 rounded-xl animate-fade-in font-medium">
          <AlertTriangle size={14} className="shrink-0 mt-0.5" />
          <span>Atenção: O bloqueio de novos lançamentos foi sugerido para esta categoria devido ao Modo Sobrevivência neste mês.</span>
        </div>
      )}

      
      <div className="flex flex-col gap-2">
        <label className="text-sm font-medium text-foreground">
          Como você se sentiu? <span className="text-[var(--accent-red)]">*</span>
        </label>
        <div className="flex flex-wrap gap-2">
          {EMOTIONS.map((emotion) => (
            <button
              key={emotion.id}
              type="button"
              onClick={() => setEmotionId(emotion.id)}
              className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1.5 text-sm font-medium transition-all duration-200 border ${emotionId === emotion.id
                  ? 'scale-105 shadow-md'
                  : 'opacity-60 hover:opacity-100'
                }`}
              style={{
                backgroundColor: emotionId === emotion.id ? `${emotion.color}20` : 'transparent',
                borderColor: emotionId === emotion.id ? emotion.color : 'var(--border-color)',
                color: emotionId === emotion.id ? emotion.color : 'var(--text-secondary)',
              }}
            >
              {emotion.label}
            </button>
          ))}
        </div>
      </div>

      
      {!isEditing && (
        <div className="flex flex-col gap-3">
          <button
            type="button"
            onClick={() => setIsRecurring(!isRecurring)}
            className={`flex items-center gap-3 rounded-xl border px-4 py-3 transition-all duration-200 ${isRecurring
                ? 'border-[var(--accent-blue)] bg-[var(--accent-blue)]/10'
                : 'border-border hover:border-[var(--accent-blue)]/50 hover:bg-surface-hover'
              }`}
          >
            <div className={`flex h-8 w-8 items-center justify-center rounded-full transition-colors ${isRecurring
                ? 'bg-[var(--accent-blue)] text-white'
                : 'bg-surface-hover text-muted'
              }`}>
              <Repeat size={16} />
            </div>
            <div className="flex-1 text-left">
              <span className={`text-sm font-medium ${isRecurring ? 'text-[var(--accent-blue)]' : 'text-foreground'}`}>
                Transação recorrente
              </span>
              <p className="text-xs text-muted">Repete todo mês automaticamente</p>
            </div>
            <div className={`h-5 w-9 rounded-full transition-colors relative ${isRecurring ? 'bg-[var(--accent-blue)]' : 'bg-border'
              }`}>
              <div className={`absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-transform ${isRecurring ? 'translate-x-4' : 'translate-x-0.5'
                }`} />
            </div>
          </button>

          
          {isRecurring && (
            <div className="flex flex-col gap-3 pl-4 border-l-2 border-[var(--accent-blue)]/30 animate-slide-up">
              <div className="flex gap-3">
                <div className="flex-1">
                  <label className="text-sm font-medium text-foreground mb-1.5 block">Dia do mês</label>
                  <input
                    type="number"
                    min={1}
                    max={31}
                    value={dayOfMonth}
                    onChange={(e) => setDayOfMonth(Math.min(31, Math.max(1, parseInt(e.target.value) || 1)))}
                    className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  />
                </div>
                <div className="flex-1">
                  <label className="text-sm font-medium text-foreground mb-1.5 block">Frequência</label>
                  <div className="flex h-10 w-full items-center rounded-md border border-border bg-surface-hover px-3 text-sm text-muted">
                    Mensal
                  </div>
                </div>
              </div>

              <div>
                <label className="text-sm font-medium text-foreground mb-1.5 block">
                  Data final <span className="text-muted font-normal">(opcional)</span>
                </label>
                <input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  min={date}
                  className="flex h-10 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                />
                <p className="text-xs text-muted mt-1">Deixe vazio para repetir indefinidamente</p>
              </div>
            </div>
          )}
        </div>
      )}

      
      <div className="flex gap-3 pt-2">
        <Button type="button" variant="ghost" className="flex-1" onClick={onCancel}>
          Cancelar
        </Button>
        <Button type="submit" className="flex-1" isLoading={isLoading}>
          {isRecurring && !isEditing ? 'Criar Recorrência' : 'Salvar'}
        </Button>
      </div>
    </form>
  );
}
