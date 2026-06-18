'use client';

import { useMemo, useState, useEffect } from 'react';
import { type TransactionOut } from '@/services/transactions.service';
import { formatCurrency } from '@/utils/formatters';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { getBalancePrediction, type BalancePrediction } from '@/services/reports.service';
import { Skeleton } from '@/components/ui/Skeleton';

interface BalanceForecastProps {
  transactions: TransactionOut[];
  periodStart: Date | null;
  periodEnd: Date | null;
  period: string;
}

export function BalanceForecast({ transactions, periodStart, periodEnd, period }: BalanceForecastProps) {
  const now = new Date();

  const isForecastMode = period === 'current_month' || (period === 'custom' && periodEnd && periodEnd.getTime() > new Date().setHours(23, 59, 59, 999));
  const isHistorical = !isForecastMode;

  const [prediction, setPrediction] = useState<BalancePrediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (!isForecastMode) return;

    let isMounted = true;
    const fetchPrediction = async () => {
      setIsLoading(true);
      try {
        const filters: any = {};
        if (period === 'current_month') {
          const nowRef = new Date();
          const m = String(nowRef.getMonth() + 1).padStart(2, '0');
          filters.month = `${nowRef.getFullYear()}-${m}`;
        } else if (period === 'custom') {
          if (periodStart) filters.start_date = periodStart.toISOString().split('T')[0];
          if (periodEnd) filters.end_date = periodEnd.toISOString().split('T')[0];
        }
        const data = await getBalancePrediction(filters);
        if (isMounted) {
          setPrediction(data);
        }
      } catch (error) {
        console.error('Error fetching balance prediction:', error);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchPrediction();

    return () => {
      isMounted = false;
    };
  }, [isForecastMode, period, periodStart, periodEnd, transactions]);

  const historicalData = useMemo(() => {
    if (!isHistorical || !periodStart || !periodEnd) return [];

    const flowByDay: Record<string, number> = {};
    transactions.forEach(tx => {
      const txDate = new Date(tx.date + 'T12:00:00');
      if (txDate >= periodStart && txDate <= periodEnd) {
        const dateStr = tx.date;
        if (!flowByDay[dateStr]) flowByDay[dateStr] = 0;
        flowByDay[dateStr] += tx.type === 'income' ? tx.amount : -tx.amount;
      }
    });

    const data = [];
    let currentBalance = 0;

    const d = new Date(periodStart);
    while (d <= periodEnd) {
      const dateStr = d.toISOString().split('T')[0];
      const displayDate = `${d.getDate().toString().padStart(2, '0')}/${(d.getMonth() + 1).toString().padStart(2, '0')}`;

      const dayFlow = flowByDay[dateStr] || 0;
      currentBalance += dayFlow;

      data.push({
        date: displayDate,
        balance: currentBalance
      });

      d.setDate(d.getDate() + 1);
    }
    return data;
  }, [transactions, isHistorical, periodStart, periodEnd]);

  if (isHistorical && historicalData.length > 0) {
    const finalBalance = historicalData[historicalData.length - 1].balance;
    const isPositive = finalBalance >= 0;

    return (
      <div className="flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted">Variação acumulada</span>
          <span className={`text-lg font-bold ${isPositive ? 'text-(--accent-green)' : 'text-(--accent-red)'}`}>
            {formatCurrency(finalBalance)}
          </span>
        </div>

        <div className="h-40 w-full mt-2">
          {mounted ? (
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
              <AreaChart data={historicalData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorBalance" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={isPositive ? 'var(--accent-green)' : 'var(--accent-red)'} stopOpacity={0.3} />
                    <stop offset="95%" stopColor={isPositive ? 'var(--accent-green)' : 'var(--accent-red)'} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <XAxis
                  dataKey="date"
                  axisLine={false}
                  tickLine={false}
                  tick={{ fontSize: 10, fill: 'var(--foreground)', opacity: 0.5 }}
                  minTickGap={20}
                />
                <Tooltip
                  contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)', backgroundColor: 'var(--surface-hover)', fontSize: '12px' }}
                  itemStyle={{ color: 'var(--foreground)' }}
                  formatter={(value: any) => [formatCurrency(Number(value || 0)), 'Saldo']}
                  labelStyle={{ color: 'var(--muted)', marginBottom: '4px' }}
                />
                <Area
                  type="monotone"
                  dataKey="balance"
                  stroke={isPositive ? 'var(--accent-green)' : 'var(--accent-red)'}
                  strokeWidth={2}
                  fillOpacity={1}
                  fill="url(#colorBalance)"
                />
              </AreaChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-full w-full" />
          )}
        </div>
      </div>
    );
  }

  if (isForecastMode && (isLoading || !prediction)) {
    return (
      <div className="flex flex-col gap-4 py-2 animate-pulse">
        <div className="flex justify-between items-center h-7">
          <Skeleton className="w-20 h-4" />
          <Skeleton className="w-24 h-5" />
        </div>
        <div className="flex justify-between items-center h-7">
          <Skeleton className="w-28 h-4" />
          <Skeleton className="w-24 h-5" />
        </div>
        <div className="flex flex-col gap-1">
          <div className="flex justify-between">
            <Skeleton className="w-24 h-3" />
            <Skeleton className="w-16 h-3" />
          </div>
          <Skeleton className="w-full h-2 rounded-full" />
        </div>
        <div className="grid grid-cols-2 gap-3 pt-1">
          <Skeleton className="h-14 rounded-xl" />
          <Skeleton className="h-14 rounded-xl" />
        </div>
        <Skeleton className="w-full h-4 mt-1" />
      </div>
    );
  }

  if (!prediction) {
    return (
      <div className="flex items-center justify-center py-6 text-sm text-muted">
        Nenhuma previsão disponível
      </div>
    );
  }

  const saldoAtualMonth = Number(prediction.current_month_balance);
  const projectedBalance = Number(prediction.predicted_end_balance);
  const trend = projectedBalance >= 0 ? 'positive' : 'negative';
  const avgDailySpending = Number(prediction.historical_daily_variable_expense_average);
  const daysRemaining = prediction.days_remaining;

  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();
  const daysInMonth = period === 'current_month'
    ? new Date(currentYear, currentMonth + 1, 0).getDate()
    : (periodStart && periodEnd ? Math.max(Math.round((periodEnd.getTime() - periodStart.getTime()) / (1000 * 60 * 60 * 24)) + 1, 1) : 30);
  const currentDay = Math.max(daysInMonth - daysRemaining, 0);

  const confidenceLabels: Record<string, string> = {
    insufficient: 'Dados insuficientes',
    low: 'Baixa',
    medium: 'Média',
    high: 'Alta'
  };
  const confidence = confidenceLabels[prediction.confidence_level] || prediction.confidence_level;

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">Saldo atual</span>
        <span className={`text-lg font-bold ${saldoAtualMonth >= 0 ? 'text-(--accent-green)' : 'text-(--accent-red)'}`}>
          {formatCurrency(saldoAtualMonth)}
        </span>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">
          {period === 'current_month' ? 'Previsão fim do mês' : 'Previsão fim do período'}
        </span>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${trend === 'positive' ? 'text-(--accent-green)' : 'text-(--accent-red)'}`}>
            {formatCurrency(projectedBalance)}
          </span>
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted">
            {period === 'current_month' ? 'Progresso do mês' : 'Progresso do período'}
          </span>
          <span className="text-xs text-muted">{currentDay}/{daysInMonth} dias</span>
        </div>
        <div className="w-full h-2 rounded-full bg-surface-hover overflow-hidden">
          <div
            className="h-full rounded-full bg-brand-500 transition-all duration-500"
            style={{ width: `${(currentDay / daysInMonth) * 100}%` }}
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3 pt-1">
        <div className="rounded-xl bg-surface-hover p-3">
          <span className="text-xs text-muted block">Média diária</span>
          <span className="text-sm font-semibold text-foreground">{formatCurrency(avgDailySpending)}/dia</span>
        </div>
        <div className="rounded-xl bg-surface-hover p-3">
          <span className="text-xs text-muted block">Dias restantes</span>
          <span className="text-sm font-semibold text-foreground">{daysRemaining} dias</span>
        </div>
      </div>

    </div>
  );
}
