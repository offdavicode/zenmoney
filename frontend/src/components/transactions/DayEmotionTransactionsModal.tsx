'use client';

import { type TransactionOut } from '@/services/transactions.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';
import { Modal } from '@/components/ui/Modal';
import { useTransactions } from '@/contexts/TransactionsContext';
import { ArrowDownLeft, ArrowUpRight, Pencil, Trash2, Repeat } from 'lucide-react';

interface DayEmotionTransactionsModalProps {
  isOpen: boolean;
  onClose: () => void;
  dateKey: string;
  emotionId: string;
  transactions: TransactionOut[];
  onEdit: (transaction: TransactionOut) => void;
  onDelete: (transaction: TransactionOut) => void;
}

export function DayEmotionTransactionsModal({
  isOpen,
  onClose,
  dateKey,
  emotionId,
  transactions,
  onEdit,
  onDelete,
}: DayEmotionTransactionsModalProps) {
  const { categories } = useTransactions();

  const emotion = EMOTIONS.find((e) => e.id === emotionId);
  const [, month, day] = dateKey.split('-');
  const formattedDate = `${day}/${month}`;

  const title = `${formattedDate} — ${emotion?.label ?? emotionId}`;

  const getCategoryLabel = (categoryId: number | null) => {
    if (categoryId === null) return 'Sem categoria';
    const cat = categories.find((c) => c.id === categoryId);
    return cat ? cat.name : String(categoryId);
  };

  const total = transactions.reduce((acc, tx) => {
    return tx.type === 'income' ? acc + tx.amount : acc - tx.amount;
  }, 0);

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      {transactions.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-12 text-muted">
          <span className="text-4xl mb-3">📭</span>
          <p className="text-sm">Nenhuma transação neste dia.</p>
        </div>
      ) : (
        <>
          <div className="divide-y divide-border -mx-6">
            {transactions.map((tx) => (
              <div
                key={tx.id}
                className="group flex items-center gap-3 px-6 py-3 hover:bg-surface-hover transition-colors"
              >


                <div className="flex flex-col gap-0.5 min-w-0 flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium text-foreground truncate">
                      {tx.description || (tx.type === 'income' ? 'Receita' : 'Despesa')}
                    </span>
                    {tx.is_recurring && (
                      <Repeat
                        size={12}
                        className="shrink-0 text-muted"
                        aria-label="Recorrente"
                      />
                    )}
                  </div>
                  <span className="text-xs text-muted truncate">
                    {getCategoryLabel(tx.category_id)}
                  </span>
                </div>

                <span
                  className={`text-sm font-semibold whitespace-nowrap ${
                    tx.type === 'income' ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
                  }`}
                >
                  {tx.type === 'income' ? '+ ' : '- '}
                  {formatCurrency(tx.amount)}
                </span>

                <div className="flex items-center gap-0.5">
                  <button
                    onClick={() => onEdit(tx)}
                    className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
                    aria-label="Editar"
                  >
                    <Pencil size={14} />
                  </button>
                  <button
                    onClick={() => onDelete(tx)}
                    className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-[var(--accent-red)] hover:bg-surface-hover transition-colors"
                    aria-label="Excluir"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between pt-4 mt-4 border-t border-border">
            <span className="text-sm font-medium text-secondary">Saldo do dia</span>
            <span
              className={`text-sm font-bold ${
                total >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'
              }`}
            >
              {formatCurrency(total)}
            </span>
          </div>
        </>
      )}
    </Modal>
  );
}
