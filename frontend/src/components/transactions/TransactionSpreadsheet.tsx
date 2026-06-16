import React, { useMemo } from 'react';
import { type TransactionOut } from '@/services/transactions.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';
import { Plus } from 'lucide-react';

interface TransactionSpreadsheetProps {
  transactions: TransactionOut[];
  currentMonth: number;
  currentYear: number;
  onAddTransaction: (date: string, emotionId?: string) => void;
  onViewDayEmotion: (dateKey: string, emotionId: string) => void;
}

export function TransactionSpreadsheet({
  transactions,
  currentMonth,
  currentYear,
  onAddTransaction,
  onViewDayEmotion,
}: TransactionSpreadsheetProps) {
  
  const daysInMonth = useMemo(() => {
    return new Date(currentYear, currentMonth + 1, 0).getDate();
  }, [currentYear, currentMonth]);

  
  const { emotionBalances, dailyBalances, emotionCounts } = useMemo(() => {
    const balances: Record<string, Record<string, number>> = {};
    const daily: Record<string, number> = {};
    const counts: Record<string, Record<string, number>> = {};

    for (let i = 1; i <= daysInMonth; i++) {
      const dayStr = String(i).padStart(2, '0');
      const dateKey = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${dayStr}`;
      balances[dateKey] = {};
      counts[dateKey] = {};
      EMOTIONS.forEach((emp) => {
        balances[dateKey][emp.id] = 0;
        counts[dateKey][emp.id] = 0;
      });
      daily[dateKey] = 0;
    }

    transactions.forEach((tx) => {
      if (!tx.emotion) return;
      const dateStr = tx.date.split('T')[0];
      if (!balances[dateStr]) return;
      if (balances[dateStr][tx.emotion] === undefined) return;

      const amount = tx.type === 'income' ? tx.amount : -tx.amount;
      balances[dateStr][tx.emotion] += amount;
      counts[dateStr][tx.emotion] += 1;
      daily[dateStr] += amount;
    });

    return { emotionBalances: balances, dailyBalances: daily, emotionCounts: counts };
  }, [transactions, currentMonth, currentYear, daysInMonth]);

  const daysArray = Array.from({ length: daysInMonth }, (_, i) => {
    const dayNum = i + 1;
    const dateKey = `${currentYear}-${String(currentMonth + 1).padStart(2, '0')}-${String(dayNum).padStart(2, '0')}`;
    return { dayNum, dateKey };
  });

  
  const getDayOfWeek = (dateKey: string) => {
    const date = new Date(dateKey + 'T12:00:00');
    return date.getDay(); 
  };

  const getDayLabel = (dateKey: string) => {
    const dow = getDayOfWeek(dateKey);
    const labels = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'];
    return labels[dow];
  };

  return (
    <div className="w-full overflow-x-auto rounded-xl border border-border shadow-sm bg-surface">
      <table className="w-full text-sm text-left border-collapse">
        <thead className="border-b border-border text-xs uppercase text-muted sticky top-0 z-10">
          
          <tr className="bg-surface-hover">
            <th
              rowSpan={2}
              className="px-3 py-3 text-center font-semibold w-20 border-r border-border bg-surface-hover"
            >
              Dia
            </th>
            {EMOTIONS.map((emotion) => (
              <th
                key={emotion.id}
                colSpan={2}
                className="px-1 py-2 text-center font-semibold border-r border-border whitespace-nowrap bg-surface-hover text-muted"
              >
                <div className="flex items-center justify-center gap-1">
                  <span>{emotion.label}</span>
                </div>
              </th>
            ))}
            <th
              rowSpan={2}
              className="sticky right-0 z-20 px-3 py-3 text-center font-semibold min-w-[100px] bg-surface-hover border-l border-border shadow-[-4px_0_8px_-4px_rgba(0,0,0,0.08)]"
            >
              Saldo do Dia
            </th>
          </tr>
          
          <tr className="bg-surface-hover/70">
            {EMOTIONS.map((emotion) => (
              <React.Fragment key={emotion.id}>
                <th className="px-1 py-1.5 text-center font-medium text-[10px] border-r border-border/50 w-10 text-muted">
                  <Plus size={10} className="mx-auto" />
                </th>
                <th className="px-1 py-1.5 text-center font-medium text-[10px] border-r border-border w-[80px] text-muted">
                  Saldo
                </th>
              </React.Fragment>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {daysArray.map(({ dayNum, dateKey }) => {
            const dailyBalance = dailyBalances[dateKey] || 0;
            const balanceColor =
              dailyBalance > 0
                ? 'text-[var(--accent-green)]'
                : dailyBalance < 0
                  ? 'text-[var(--accent-red)]'
                  : 'text-muted';
            const dow = getDayOfWeek(dateKey);
            const isWeekend = dow === 0 || dow === 6;

            return (
              <tr
                key={dateKey}
                className={`hover:bg-surface-hover/50 transition-colors ${isWeekend ? 'bg-surface-hover/20' : ''}`}
              >
                
                <td className="px-2 py-2 text-center border-r border-border bg-surface-hover/30">
                  <div className="flex flex-col items-center">
                    <span className="font-semibold text-foreground text-sm">{dayNum}</span>
                    <span className={`text-[10px] ${isWeekend ? 'text-[var(--accent-red)]/70' : 'text-muted'}`}>
                      {getDayLabel(dateKey)}
                    </span>
                  </div>
                </td>

                
                {EMOTIONS.map((emotion) => {
                  const balance = emotionBalances[dateKey]?.[emotion.id] || 0;
                  const count = emotionCounts[dateKey]?.[emotion.id] || 0;
                  const cellBalanceColor =
                    balance > 0
                      ? 'text-[var(--accent-green)]'
                      : balance < 0
                        ? 'text-[var(--accent-red)]'
                        : 'text-muted';

                  return (
                    <React.Fragment key={emotion.id}>
                      
                      <td className="border-r border-border/50 p-0 w-10 align-middle">
                        <button
                          onClick={() => onAddTransaction(dateKey, emotion.id)}
                          className="w-full h-full min-h-[40px] flex items-center justify-center text-muted hover:text-foreground hover:bg-black/5 dark:hover:bg-white/5 transition-colors"
                          title={`Adicionar em ${dayNum} — ${emotion.label}`}
                        >
                          <Plus size={14} className="opacity-40 hover:opacity-100 transition-opacity" />
                        </button>
                      </td>

                      
                      <td className="border-r border-border p-0 w-[80px] align-middle">
                        {count > 0 ? (
                          <button
                            onClick={() => onViewDayEmotion(dateKey, emotion.id)}
                            className={`w-full h-full min-h-[40px] flex flex-col items-center justify-center px-1 py-1 hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer group`}
                            title={`${count} transação(ões) — clique para ver`}
                          >
                            <span className={`text-xs font-semibold ${cellBalanceColor}`}>
                              {formatCurrency(Math.abs(balance)).replace('R$', '').trim()}
                            </span>
                            <span className="text-[9px] text-muted group-hover:text-secondary transition-colors">
                              {count} {count === 1 ? 'lançamento' : 'lançamentos'}
                            </span>
                          </button>
                        ) : (
                          <div className="w-full min-h-[40px] flex items-center justify-center" />
                        )}
                      </td>
                    </React.Fragment>
                  );
                })}

                
                <td className={`sticky right-0 z-10 px-3 py-2 text-center font-bold whitespace-nowrap border-l border-border shadow-[-4px_0_8px_-4px_rgba(0,0,0,0.08)] ${isWeekend ? 'bg-surface-hover' : 'bg-surface'} ${balanceColor}`}>
                  {dailyBalance !== 0 ? formatCurrency(dailyBalance) : ''}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
