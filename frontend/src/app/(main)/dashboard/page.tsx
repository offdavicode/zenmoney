'use client';

import { useState, useMemo } from 'react';
import { useTransactions } from '@/contexts/TransactionsContext';
import { useAuth } from '@/contexts/AuthContext';
import { Card } from '@/components/ui/Card';
import { ExpensePieChart } from '@/components/charts/ExpensePieChart';
import { EmotionPieChart } from '@/components/charts/EmotionPieChart';
import { CategoryBarChart } from '@/components/charts/CategoryBarChart';
import { EmotionBarChart } from '@/components/charts/EmotionBarChart';
import { EmotionCrossChart } from '@/components/charts/EmotionCrossChart';
import { SurvivalMode } from '@/components/dashboard/SurvivalMode';
import { BalanceForecast } from '@/components/dashboard/BalanceForecast';
import { formatCurrency } from '@/utils/formatters';
import { ArrowDownLeft, ArrowUpRight, MoreVertical } from 'lucide-react';

export default function DashboardPage() {
  const { transactions } = useTransactions();
  const { user } = useAuth();

  const [period, setPeriod] = useState('current_month');
  const [customStartDate, setCustomStartDate] = useState('');
  const [customEndDate, setCustomEndDate] = useState('');

  
  const [proportionType, setProportionType] = useState<'category' | 'emotion'>('category');
  const [rankingType, setRankingType] = useState<'category' | 'emotion'>('category');

  
  const [showProportionMenu, setShowProportionMenu] = useState(false);
  const [showRankingMenu, setShowRankingMenu] = useState(false);

  const now = useMemo(() => new Date(), []);

  const { periodStart, periodEnd } = useMemo(() => {
    let start: Date | null = null;
    let end: Date | null = null;

    if (period === 'current_month') {
      start = new Date(now.getFullYear(), now.getMonth(), 1);
      end = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59);
    } else if (period === 'last_month') {
      start = new Date(now.getFullYear(), now.getMonth() - 1, 1);
      end = new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59);
    } else if (period === 'last_7_days') {
      start = new Date(now);
      start.setDate(now.getDate() - 7);
      start.setHours(0, 0, 0, 0);
      end = new Date(now);
    } else if (period === 'last_30_days') {
      start = new Date(now);
      start.setDate(now.getDate() - 30);
      start.setHours(0, 0, 0, 0);
      end = new Date(now);
    } else if (period === 'custom') {
      if (customStartDate) start = new Date(customStartDate + 'T00:00:00');
      if (customEndDate) end = new Date(customEndDate + 'T23:59:59');
    }

    return { periodStart: start, periodEnd: end };
  }, [period, customStartDate, customEndDate, now]);

  
  const filteredTx = useMemo(() => {
    return transactions.filter(tx => {
      if (period === 'all') return true;

      const txDate = new Date(tx.date + 'T12:00:00');

      if (periodStart && txDate < periodStart) return false;
      if (periodEnd && txDate > periodEnd) return false;

      return true;
    });
  }, [transactions, period, periodStart, periodEnd]);

  
  const incomeTxs = useMemo(() => filteredTx.filter((tx) => tx.type === 'income'), [filteredTx]);
  const expenseTxs = useMemo(() => filteredTx.filter((tx) => tx.type === 'expense'), [filteredTx]);

  const totalReceitas = useMemo(() => incomeTxs.reduce((acc, tx) => acc + tx.amount, 0), [incomeTxs]);
  const totalDespesas = useMemo(() => expenseTxs.reduce((acc, tx) => acc + tx.amount, 0), [expenseTxs]);

  const maxIncome = useMemo(() => incomeTxs.length > 0 ? Math.max(...incomeTxs.map(t => t.amount)) : 0, [incomeTxs]);
  const maxExpense = useMemo(() => expenseTxs.length > 0 ? Math.max(...expenseTxs.map(t => t.amount)) : 0, [expenseTxs]);

  const selectedMonth = useMemo(() => {
    let d = now;
    if (period === 'last_month') {
      d = new Date(now.getFullYear(), now.getMonth() - 1, 1);
    } else if (period === 'custom' && customEndDate) {
      d = new Date(customEndDate + 'T12:00:00');
    }
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`;
  }, [period, customEndDate, now]);

  const greeting = () => {
    const hour = now.getHours();
    if (hour < 12) return 'Bom dia';
    if (hour < 18) return 'Boa tarde';
    return 'Boa noite';
  };

  return (
    <div className="flex flex-col gap-6">
      
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
          {greeting()}, <span className="text-muted">{user?.name?.split(' ')[0] || 'Usuário'}</span>!
        </h1>

        <div className="flex flex-col sm:flex-row gap-2 items-center">
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value)}
            className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary w-full sm:w-auto"
          >
            <option value="current_month">Este Mês</option>
            <option value="last_month">Último Mês</option>
            <option value="last_7_days">Últimos 7 dias</option>
            <option value="last_30_days">Últimos 30 dias</option>
            <option value="custom">Personalizado...</option>
          </select>

          {period === 'custom' && (
            <div className="flex items-center gap-2 w-full sm:w-auto animate-fade-in">
              <input
                type="date"
                value={customStartDate}
                max={customEndDate || undefined}
                onChange={e => {
                  const val = e.target.value;
                  setCustomStartDate(val);
                  if (customEndDate && val > customEndDate) {
                    setCustomEndDate(val);
                  }
                }}
                className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary w-full sm:w-36"
              />
              <span className="text-muted text-sm">até</span>
              <input
                type="date"
                value={customEndDate}
                min={customStartDate || undefined}
                onChange={e => {
                  const val = e.target.value;
                  setCustomEndDate(val);
                  if (customStartDate && val < customStartDate) {
                    setCustomStartDate(val);
                  }
                }}
                className="h-10 rounded-md border border-border bg-surface px-3 py-2 text-sm text-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary w-full sm:w-36"
              />
            </div>
          )}
        </div>
      </div>

      
      <SurvivalMode month={selectedMonth} />

      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

        {/* COLUNA 1 */}
        <div className="flex flex-col gap-6">
          {/* Card Entradas */}
          <Card className="rounded-3xl !gap-2">
            <div className="flex items-start justify-between">
              <h3 className="text-sm font-medium text-muted">Entradas</h3>
            </div>
            <div className="flex items-center justify-between mt-1">
              <p className="text-2xl font-bold text-[var(--accent-green)]">
                {formatCurrency(totalReceitas)}
              </p>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted">
                {incomeTxs.length} transações no período
              </span>
              <span className="text-xs text-muted">
                Maior entrada: <span className="font-semibold text-foreground">{formatCurrency(maxIncome)}</span>
              </span>
            </div>
          </Card>

          {/* Card Sentimento x Consumo */}
          <Card className="rounded-3xl flex-1">
            <div className="flex items-start justify-between mb-4">
              <h3 className="text-base font-bold text-foreground">Sentimento x Consumo</h3>
            </div>
            <div className="mt-4">
              <EmotionCrossChart transactions={filteredTx} />
            </div>
          </Card>
        </div>

        {/* COLUNA 2 */}
        <div className="flex flex-col gap-6">
          {/* Card Saídas */}
          <Card className="rounded-3xl !gap-2">
            <div className="flex items-start justify-between">
              <h3 className="text-sm font-medium text-muted">Saídas</h3>
            </div>
            <div className="flex items-center justify-between mt-1">
              <p className="text-2xl font-bold text-[var(--accent-red)]">
                {formatCurrency(totalDespesas)}
              </p>
            </div>
            <div className="flex flex-col gap-0.5">
              <span className="text-xs text-muted">
                {expenseTxs.length} transações no período
              </span>
              <span className="text-xs text-muted">
                Maior despesa: <span className="font-semibold text-foreground">{formatCurrency(maxExpense)}</span>
              </span>
            </div>
          </Card>

          {/* Card Proporção de Gastos */}
          <Card className="rounded-3xl flex-1 relative">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-foreground">Proporção de Gastos</h3>
                <p className="text-xs text-muted font-medium mt-0.5">
                  {proportionType === 'category' ? 'Por categoria' : 'Por emoção'}
                </p>
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowProportionMenu(!showProportionMenu)}
                  className="text-muted hover:text-foreground transition-colors p-1 rounded-full hover:bg-surface-hover"
                >
                  <MoreVertical size={18} />
                </button>
                {showProportionMenu && (
                  <div className="absolute right-0 mt-1 w-28 rounded-xl border border-border bg-surface p-1 shadow-lg z-10 animate-fade-in">
                    <button
                      onClick={() => {
                        setProportionType('category');
                        setShowProportionMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${proportionType === 'category' ? 'bg-surface-hover text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                        }`}
                    >
                      Categoria
                    </button>
                    <button
                      onClick={() => {
                        setProportionType('emotion');
                        setShowProportionMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${proportionType === 'emotion' ? 'bg-surface-hover text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                        }`}
                    >
                      Emoção
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 flex flex-col justify-center">
              {proportionType === 'category' ? (
                <ExpensePieChart transactions={filteredTx} />
              ) : (
                <EmotionPieChart transactions={filteredTx} />
              )}
            </div>
          </Card>
        </div>

        {/* COLUNA 3 */}
        <div className="flex flex-col gap-6">
          {/* Card Previsão do Saldo */}
          <Card className="rounded-3xl !gap-2">
            <div className="flex items-start justify-between">
              <h3 className="text-sm font-medium text-muted">
                {period === 'current_month' || (period === 'custom' && periodEnd && periodEnd.getTime() > new Date().setHours(23, 59, 59, 999))
                  ? 'Previsão do Saldo'
                  : 'Variação do Saldo'}
              </h3>
            </div>
            <div className="mt-1">
              <BalanceForecast
                transactions={transactions}
                periodStart={periodStart}
                periodEnd={periodEnd}
                period={period}
              />
            </div>
          </Card>

          {/* Card Ranking de Despesas */}
          <Card className="rounded-3xl flex-1 relative">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-foreground">Ranking de Despesas</h3>
                <p className="text-xs text-muted font-medium mt-0.5">
                  {rankingType === 'category' ? 'Por categoria' : 'Por emoção'}
                </p>
              </div>
              <div className="relative">
                <button
                  onClick={() => setShowRankingMenu(!showRankingMenu)}
                  className="text-muted hover:text-foreground transition-colors p-1 rounded-full hover:bg-surface-hover"
                >
                  <MoreVertical size={18} />
                </button>
                {showRankingMenu && (
                  <div className="absolute right-0 mt-1 w-38 rounded-xl border border-border bg-surface p-1 shadow-lg z-10 animate-fade-in">
                    <button
                      onClick={() => {
                        setRankingType('category');
                        setShowRankingMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${rankingType === 'category' ? 'bg-surface-hover text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                        }`}
                    >
                      Top 10 Categorias
                    </button>
                    <button
                      onClick={() => {
                        setRankingType('emotion');
                        setShowRankingMenu(false);
                      }}
                      className={`w-full text-left px-3 py-2 text-xs font-semibold rounded-lg transition-colors ${rankingType === 'emotion' ? 'bg-surface-hover text-foreground' : 'text-muted hover:bg-surface-hover hover:text-foreground'
                        }`}
                    >
                      Top 10 Emoções
                    </button>
                  </div>
                )}
              </div>
            </div>

            <div className="flex-1 flex flex-col justify-center">
              {rankingType === 'category' ? (
                <CategoryBarChart transactions={filteredTx} />
              ) : (
                <EmotionBarChart transactions={filteredTx} />
              )}
            </div>
          </Card>
        </div>

      </div>
    </div>
  );
}
