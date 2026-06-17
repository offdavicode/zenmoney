'use client';

import { useState, useMemo, useEffect } from 'react';
import { useTransactions } from '@/contexts/TransactionsContext';
import { Button } from '@/components/ui/Button';
import { Modal } from '@/components/ui/Modal';
import { TransactionForm } from '@/components/transactions/TransactionForm';
import { TransactionSpreadsheet } from '@/components/transactions/TransactionSpreadsheet';
import { DayEmotionTransactionsModal } from '@/components/transactions/DayEmotionTransactionsModal';
import { RecurrenceConfirmDialog } from '@/components/transactions/RecurrenceConfirmDialog';
import { type TransactionOut, type TransactionCreate } from '@/services/transactions.service';
import { type RecurrenceCreate, type RecurrenceUpdate } from '@/services/recurrences.service';
import { getSurvivalModeReport } from '@/services/reports.service';
import { MONTHS } from '@/utils/constants';
import { Plus, ChevronLeft, ChevronRight } from 'lucide-react';

export default function LancamentosPage() {
  const {
    transactions,
    addTransaction,
    deleteTransaction,
    updateTransaction,
    addRecurrence,
    updateRecurrence,
    pauseRecurrence,
    deleteRecurrenceAndFuture,
    generateRecurrences,
  } = useTransactions();

  const [currentMonth, setCurrentMonth] = useState(new Date().getMonth());
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [highlightedTxIds, setHighlightedTxIds] = useState<number[]>([]);

  useEffect(() => {
    let isMounted = true;
    async function loadSurvivalReport() {
      try {
        const monthStr = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}`;
        const report = await getSurvivalModeReport({ month: monthStr });
        if (isMounted) {
          setHighlightedTxIds(report?.highlighted_transaction_ids || []);
        }
      } catch (e) {
        console.error('Erro ao carregar relatório sobrevivência para lançamentos:', e);
      }
    }
    loadSurvivalReport();
    return () => {
      isMounted = false;
    };
  }, [currentYear, currentMonth, transactions]);

  
  useEffect(() => {
    generateRecurrences(currentYear, currentMonth);
  }, [currentYear, currentMonth, generateRecurrences]);

  
  const [isFormModalOpen, setIsFormModalOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | undefined>();
  const [selectedEmotionId, setSelectedEmotionId] = useState<string | undefined>();
  const [selectedTransaction, setSelectedTransaction] = useState<TransactionOut | undefined>();

  
  const [dayEmotionModal, setDayEmotionModal] = useState<{
    isOpen: boolean;
    dateKey: string;
    emotionId: string;
  }>({ isOpen: false, dateKey: '', emotionId: '' });

  
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    mode: 'edit' | 'delete';
    transaction: TransactionOut | null;
  }>({ isOpen: false, mode: 'delete', transaction: null });

  
  const [editAllFuture, setEditAllFuture] = useState(false);

  
  const prevMonth = () => {
    if (currentMonth === 0) {
      setCurrentMonth(11);
      setCurrentYear(currentYear - 1);
    } else {
      setCurrentMonth(currentMonth - 1);
    }
  };

  const nextMonth = () => {
    if (currentMonth === 11) {
      setCurrentMonth(0);
      setCurrentYear(currentYear + 1);
    } else {
      setCurrentMonth(currentMonth + 1);
    }
  };

  
  const filteredTransactions = useMemo(() => {
    return transactions.filter((tx) => {
      const txDate = new Date(tx.date + 'T12:00:00');
      return txDate.getMonth() === currentMonth && txDate.getFullYear() === currentYear;
    });
  }, [transactions, currentMonth, currentYear]);

  
  const dayEmotionTransactions = useMemo(() => {
    if (!dayEmotionModal.isOpen) return [];
    return filteredTransactions.filter(
      (tx) => tx.date.split('T')[0] === dayEmotionModal.dateKey && tx.emotion === dayEmotionModal.emotionId
    );
  }, [filteredTransactions, dayEmotionModal]);

  

  
  const handleOpenNewTransaction = (date?: string, emotionId?: string) => {
    setSelectedDate(date);
    setSelectedEmotionId(emotionId);
    setSelectedTransaction(undefined);
    setEditAllFuture(false);
    setIsFormModalOpen(true);
  };

  
  const handleViewDayEmotion = (dateKey: string, emotionId: string) => {
    setDayEmotionModal({ isOpen: true, dateKey, emotionId });
  };

  
  const handleEditFromList = (tx: TransactionOut) => {
    if (tx.is_recurring && tx.recurrence_id) {
      setConfirmDialog({ isOpen: true, mode: 'edit', transaction: tx });
    } else {
      setSelectedTransaction(tx);
      setSelectedDate(undefined);
      setSelectedEmotionId(undefined);
      setEditAllFuture(false);
      setDayEmotionModal((prev) => ({ ...prev, isOpen: false }));
      setIsFormModalOpen(true);
    }
  };

  
  const handleDeleteFromList = (tx: TransactionOut) => {
    if (tx.is_recurring && tx.recurrence_id) {
      setConfirmDialog({ isOpen: true, mode: 'delete', transaction: tx });
    } else {
      if (confirm('Tem certeza que deseja excluir esta transação?')) {
        deleteTransaction(tx.id);
      }
    }
  };

  
  const handleConfirmSingle = async () => {
    const tx = confirmDialog.transaction;
    if (!tx) return;

    if (confirmDialog.mode === 'delete') {
      await deleteTransaction(tx.id);
      setConfirmDialog({ isOpen: false, mode: 'delete', transaction: null });
    } else {
      
      setSelectedTransaction(tx);
      setSelectedDate(undefined);
      setSelectedEmotionId(undefined);
      setEditAllFuture(false);
      setConfirmDialog({ isOpen: false, mode: 'edit', transaction: null });
      setDayEmotionModal((prev) => ({ ...prev, isOpen: false }));
      setIsFormModalOpen(true);
    }
  };

  
  const handleConfirmAll = async () => {
    const tx = confirmDialog.transaction;
    if (!tx) return;

    if (confirmDialog.mode === 'delete') {
      await deleteTransaction(tx.id);
      if (tx.recurrence_id) {
        await deleteRecurrenceAndFuture(tx.recurrence_id);
      }
      setConfirmDialog({ isOpen: false, mode: 'delete', transaction: null });
    } else {
      
      setSelectedTransaction(tx);
      setSelectedDate(undefined);
      setSelectedEmotionId(undefined);
      setEditAllFuture(true);
      setConfirmDialog({ isOpen: false, mode: 'edit', transaction: null });
      setDayEmotionModal((prev) => ({ ...prev, isOpen: false }));
      setIsFormModalOpen(true);
    }
  };

  
  const handleFormSubmit = async (tx: TransactionCreate, id?: number) => {
    if (id) {
      await updateTransaction(id, tx);
      
      if (editAllFuture && selectedTransaction?.recurrence_id) {
        const recurrenceUpdate: RecurrenceUpdate = {
          type: tx.type,
          amount: tx.amount,
          description: tx.description,
          category_id: tx.category_id,
          emotion: tx.emotion,
        };
        await updateRecurrence(selectedTransaction.recurrence_id, recurrenceUpdate);
      }
    } else {
      await addTransaction(tx);
    }
    setIsFormModalOpen(false);
    setEditAllFuture(false);
  };

  
  const handleRecurrenceSubmit = async (recurrence: RecurrenceCreate) => {
    await addRecurrence(recurrence);
    setIsFormModalOpen(false);
  };

  const yearSuffix = String(currentYear).slice(-2);

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <button
              onClick={prevMonth}
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
              aria-label="Mês anterior"
            >
              <ChevronLeft size={20} />
            </button>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
              {MONTHS[currentMonth]}/{yearSuffix}
            </h1>
            <button
              onClick={nextMonth}
              className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
              aria-label="Próximo mês"
            >
              <ChevronRight size={20} />
            </button>
          </div>
        </div>

        <Button onClick={() => handleOpenNewTransaction()} className="gap-2 shadow-md">
          <Plus size={18} />
          <span className="hidden sm:inline">Adicionar transação</span>
          <span className="sm:hidden">Novo</span>
        </Button>
      </div>

      
      <TransactionSpreadsheet
        transactions={filteredTransactions}
        currentMonth={currentMonth}
        currentYear={currentYear}
        onAddTransaction={handleOpenNewTransaction}
        onViewDayEmotion={handleViewDayEmotion}
        highlightedTransactionIds={highlightedTxIds}
      />

      
      <Modal
        isOpen={isFormModalOpen}
        onClose={() => { setIsFormModalOpen(false); setEditAllFuture(false); }}
        title={selectedTransaction ? (editAllFuture ? 'Editar transação e futuras' : 'Editar transação') : 'Nova transação'}
      >
        {isFormModalOpen && (
          <TransactionForm
            initialDate={selectedDate}
            initialEmotionId={selectedEmotionId}
            initialTransaction={selectedTransaction}
            onSubmit={handleFormSubmit}
            onSubmitRecurrence={handleRecurrenceSubmit}
            onCancel={() => { setIsFormModalOpen(false); setEditAllFuture(false); }}
          />
        )}
      </Modal>

      
      <DayEmotionTransactionsModal
        isOpen={dayEmotionModal.isOpen}
        onClose={() => setDayEmotionModal({ isOpen: false, dateKey: '', emotionId: '' })}
        dateKey={dayEmotionModal.dateKey}
        emotionId={dayEmotionModal.emotionId}
        transactions={dayEmotionTransactions}
        onEdit={handleEditFromList}
        onDelete={handleDeleteFromList}
      />

      
      <RecurrenceConfirmDialog
        isOpen={confirmDialog.isOpen}
        onClose={() => setConfirmDialog({ isOpen: false, mode: 'delete', transaction: null })}
        mode={confirmDialog.mode}
        onConfirmSingle={handleConfirmSingle}
        onConfirmAll={handleConfirmAll}
      />
    </div>
  );
}
