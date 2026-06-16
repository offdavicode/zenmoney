'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { type TransactionOut } from '@/services/transactions.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';

interface EmotionPieChartProps {
  transactions: TransactionOut[];
}

export function EmotionPieChart({ transactions }: EmotionPieChartProps) {
  const expenses = transactions.filter((tx) => tx.type === 'expense');

  
  const emotionMap = new Map<string, number>();
  expenses.forEach((tx) => {
    const eid = tx.emotion || 'nao_informado';
    const current = emotionMap.get(eid) || 0;
    emotionMap.set(eid, current + tx.amount);
  });

  const data = Array.from(emotionMap.entries())
    .map(([emotionId, value]) => {
      if (emotionId === 'nao_informado') {
        return { name: 'Não Informado', value, color: '#94A3B8' };
      }
      const em = EMOTIONS.find((e) => e.id === emotionId);
      return {
        name: em ? em.label : (emotionId.charAt(0).toUpperCase() + emotionId.slice(1)),
        value,
        color: em?.color || '#94A3B8',
      };
    })
    .sort((a, b) => b.value - a.value);

  const total = data.reduce((acc, d) => acc + d.value, 0);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: any) => [formatCurrency(Number(value)), 'Valor']}
              contentStyle={{
                backgroundColor: 'var(--surface)',
                border: '1px solid var(--border-color)',
                borderRadius: '12px',
                fontSize: '13px',
              }}
            />
          </PieChart>
        </ResponsiveContainer>
      </div>

      
      <div className="flex flex-col gap-2 max-h-[220px] overflow-y-auto pr-1">
        {data.map((entry, index) => {
          const pct = total > 0 ? ((entry.value / total) * 100).toFixed(0) : 0;
          return (
            <div key={index} className="flex items-center justify-between text-xs border-b border-border/50 pb-1.5 last:border-0 last:pb-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
                <span className="text-secondary font-medium">{entry.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">{formatCurrency(entry.value)}</span>
                <span className="text-muted">({pct}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
