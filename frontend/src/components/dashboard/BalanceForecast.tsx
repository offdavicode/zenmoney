'use client';

import { useMemo } from 'react';
import { type TransactionOut } from '@/services/transactions.service';
import { formatCurrency } from '@/utils/formatters';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { AreaChart, Area, XAxis, Tooltip, ResponsiveContainer } from 'recharts';

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

  
  const currentMonth = now.getMonth();
  const currentYear = now.getFullYear();
  const daysInMonth = new Date(currentYear, currentMonth + 1, 0).getDate();
  const currentDay = now.getDate();
  const daysRemaining = daysInMonth - currentDay;

  const monthTx = transactions.filter((tx) => {
    const d = new Date(tx.date + 'T12:00:00');
    return d.getMonth() === currentMonth && d.getFullYear() === currentYear;
  });

  const totalReceitasMonth = monthTx.filter((tx) => tx.type === 'income').reduce((acc, tx) => acc + tx.amount, 0);
  const totalDespesasMonth = monthTx.filter((tx) => tx.type === 'expense').reduce((acc, tx) => acc + tx.amount, 0);
  const saldoAtualMonth = totalReceitasMonth - totalDespesasMonth;

  const avgDailySpending = currentDay > 0 ? totalDespesasMonth / currentDay : 0;
  const projectedSpending = totalDespesasMonth + avgDailySpending * daysRemaining;
  const projectedBalance = totalReceitasMonth - projectedSpending;
  const trend = projectedBalance >= 0 ? 'positive' : 'negative';

  
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
          <span className={`text-lg font-bold ${isPositive ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
            {formatCurrency(finalBalance)}
          </span>
        </div>

        <div className="h-40 w-full mt-2">
          <ResponsiveContainer width="100%" height="100%">
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
        </div>
      </div>
    );
  }

  
  return (
    <div className="flex flex-col gap-4">
      
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">Saldo atual</span>
        <span className={`text-lg font-bold ${saldoAtualMonth >= 0 ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
          {formatCurrency(saldoAtualMonth)}
        </span>
      </div>

      
      <div className="flex items-center justify-between">
        <span className="text-sm text-muted">Previsão fim do mês</span>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-bold ${trend === 'positive' ? 'text-[var(--accent-green)]' : 'text-[var(--accent-red)]'}`}>
            {formatCurrency(projectedBalance)}
          </span>
        </div>
      </div>

      
      <div>
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted">Progresso do mês</span>
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

      
      <div className="flex items-center gap-2 text-xs text-muted">
        <Minus size={12} />
        <span>Previsão baseada na média de gastos diários do mês atual.</span>
      </div>
    </div>
  );
}
