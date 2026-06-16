'use client';

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react';
import { listTransactions, createTransaction, updateTransaction as apiUpdateTransaction, deleteTransaction as apiDeleteTransaction, TransactionOut, TransactionCreate } from '@/services/transactions.service';
import { listCategories, CategoryOut } from '@/services/categories.service';
import {
  createRecurrence as apiCreateRecurrence,
  updateRecurrence as apiUpdateRecurrence,
  pauseRecurrence as apiPauseRecurrence,
  runDueRecurrences,
  RecurrenceCreate,
  RecurrenceUpdate,
} from '@/services/recurrences.service';
import { useAuth } from './AuthContext';

interface TransactionsContextType {
  transactions: TransactionOut[];
  categories: CategoryOut[];
  isLoading: boolean;
  addTransaction: (tx: TransactionCreate) => Promise<void>;
  deleteTransaction: (id: number) => Promise<void>;
  updateTransaction: (id: number, tx: Partial<TransactionCreate>) => Promise<void>;
  addRecurrence: (data: RecurrenceCreate) => Promise<void>;
  updateRecurrence: (id: number, data: RecurrenceUpdate) => Promise<void>;
  pauseRecurrence: (id: number) => Promise<void>;
  deleteRecurrenceAndFuture: (recurrenceId: number) => Promise<void>;
  generateRecurrences: (year: number, month: number) => Promise<void>;
  refreshTransactions: () => Promise<void>;
  budgetUpdatedVersion: number;
  notifyBudgetUpdated: () => void;
}

const TransactionsContext = createContext<TransactionsContextType | undefined>(undefined);

export function TransactionsProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  const [transactions, setTransactions] = useState<TransactionOut[]>([]);
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [budgetUpdatedVersion, setBudgetUpdatedVersion] = useState(0);

  const notifyBudgetUpdated = useCallback(() => {
    setBudgetUpdatedVersion((prev) => prev + 1);
  }, []);

  const fetchData = useCallback(async () => {
    if (!isAuthenticated) return;
    setIsLoading(true);
    try {
      const [txs, cats] = await Promise.all([
        listTransactions(),
        listCategories(),
      ]);
      setTransactions(txs);
      setCategories(cats);

      const dueResult = await runDueRecurrences();
      if (dueResult.generated_count > 0) {
        const updatedTxs = await listTransactions();
        setTransactions(updatedTxs);
      }
    } catch (error) {
      console.error('Failed to fetch transactions or categories', error);
    } finally {
      setIsLoading(false);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const addTransaction = async (tx: TransactionCreate) => {
    const newTx = await createTransaction(tx);
    setTransactions((prev) => [newTx, ...prev]);
  };

  const deleteTransaction = async (id: number) => {
    await apiDeleteTransaction(id);
    setTransactions((prev) => prev.filter((tx) => tx.id !== id));
  };

  const updateTransaction = async (id: number, updated: Partial<TransactionCreate>) => {
    const newTx = await apiUpdateTransaction(id, updated);
    setTransactions((prev) =>
      prev.map((tx) => (tx.id === id ? newTx : tx))
    );
  };

  const addRecurrence = async (data: RecurrenceCreate) => {
    await apiCreateRecurrence(data);
    await runDueRecurrences();
    const updatedTxs = await listTransactions();
    setTransactions(updatedTxs);
  };

  const updateRecurrence = async (id: number, data: RecurrenceUpdate) => {
    await apiUpdateRecurrence(id, data);
    const updatedTxs = await listTransactions();
    setTransactions(updatedTxs);
  };

  const pauseRecurrence = async (id: number) => {
    await apiPauseRecurrence(id);
  };

  const deleteRecurrenceAndFuture = async (recurrenceId: number) => {
    await apiPauseRecurrence(recurrenceId);
    const updatedTxs = await listTransactions();
    setTransactions(updatedTxs);
  };

  const generateRecurrences = async (year: number, month: number) => {
    
    const lastDay = new Date(year, month + 1, 0).getDate();
    const throughDate = `${year}-${String(month + 1).padStart(2, '0')}-${String(lastDay).padStart(2, '0')}`;
    
    const dueResult = await runDueRecurrences(throughDate);
    if (dueResult.generated_count > 0) {
      const updatedTxs = await listTransactions();
      setTransactions(updatedTxs);
    }
  };

  return (
    <TransactionsContext.Provider
      value={{
        transactions,
        categories,
        isLoading,
        addTransaction,
        deleteTransaction,
        updateTransaction,
        addRecurrence,
        updateRecurrence,
        pauseRecurrence,
        deleteRecurrenceAndFuture,
        generateRecurrences,
        refreshTransactions: fetchData,
        budgetUpdatedVersion,
        notifyBudgetUpdated,
      }}
    >
      {children}
    </TransactionsContext.Provider>
  );
}

export function useTransactions() {
  const context = useContext(TransactionsContext);
  if (context === undefined) {
    throw new Error('useTransactions must be used within a TransactionsProvider');
  }
  return context;
}
