'use client';

import { useTransactions } from '@/contexts/TransactionsContext';
import { type TransactionOut } from '@/services/transactions.service';
import { formatCurrency, formatDateBR } from '@/utils/formatters';
import { EmotionTag } from '@/components/ui/EmotionTag';
import { ArrowDownLeft, ArrowUpRight, Trash2, Pencil } from 'lucide-react';

interface TransactionListProps {
  transactions: TransactionOut[];
  onDelete: (id: number) => void;
  onEdit: (transaction: TransactionOut) => void;
}

export function TransactionList({ transactions, onDelete, onEdit }: TransactionListProps) {
  const { categories } = useTransactions();

  const getCategoryLabel = (categoryId: number | null) => {
    if (categoryId === null) return 'Sem categoria';
    const cat = categories.find((c) => c.id === categoryId);
    return cat ? cat.name : String(categoryId);
  };

  if (transactions.length === 0) return null;

  return (
    <div className="glass-card overflow-hidden">
      
      <div className="hidden md:grid grid-cols-[1fr_1fr_1fr_auto_auto] gap-4 px-6 py-3 border-b border-border text-xs font-medium text-muted uppercase tracking-wider">
        <span>Descrição</span>
        <span>Categoria</span>
        <span>Data</span>
        <span className="text-right">Valor</span>
        <span className="w-20"></span>
      </div>

      
      <div className="divide-y divide-border">
        {transactions.map((tx) => (
          <div
            key={tx.id}
            className="group flex flex-col md:grid md:grid-cols-[1fr_1fr_1fr_auto_auto] gap-2 md:gap-4 px-6 py-4 hover:bg-surface-hover transition-colors"
          >
            
            <div className="flex items-center gap-3">
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full ${
                  tx.type === 'income'
                    ? 'bg-[var(--accent-green)]/10 text-[var(--accent-green)]'
                    : 'bg-[var(--accent-red)]/10 text-[var(--accent-red)]'
                }`}
              >
                {tx.type === 'income' ? (
                  <ArrowDownLeft size={16} />
                ) : (
                  <ArrowUpRight size={16} />
                )}
              </div>
              <div className="flex flex-col gap-0.5 min-w-0">
                <span className="text-sm font-medium text-foreground truncate">
                  {tx.description || (tx.type === 'income' ? 'Receita' : 'Despesa')}
                </span>
                {tx.emotion && <EmotionTag emotionId={tx.emotion} />}
              </div>
            </div>

            <div className="flex items-center text-sm text-secondary md:pl-0 pl-12">
              {getCategoryLabel(tx.category_id)}
            </div>

            
            <div className="flex items-center text-sm text-muted md:pl-0 pl-12">
              {formatDateBR(tx.date)}
            </div>

            
            <div className="flex items-center md:pl-0 pl-12">
              <span
                className={`text-sm font-semibold whitespace-nowrap ${
                  tx.type === 'income' ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
                }`}
              >
                {tx.type === 'income' ? '+ ' : '- '}
                {formatCurrency(tx.amount)}
              </span>
            </div>

            
            <div className="flex items-center justify-end gap-1 w-20 md:opacity-0 md:group-hover:opacity-100 transition-opacity pl-12 md:pl-0">
              <button
                onClick={() => onEdit(tx)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
                aria-label="Editar"
              >
                <Pencil size={14} />
              </button>
              <button
                onClick={() => onDelete(tx.id)}
                className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-[var(--accent-red)] hover:bg-surface-hover transition-colors"
                aria-label="Excluir"
              >
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
