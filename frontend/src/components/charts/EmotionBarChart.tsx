'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { type TransactionOut } from '@/services/transactions.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';

interface EmotionBarChartProps {
  transactions: TransactionOut[];
}

export function EmotionBarChart({ transactions }: EmotionBarChartProps) {
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
        return {
          name: 'Não Informado',
          value,
          color: '#94A3B8',
        };
      }
      const em = EMOTIONS.find((e) => e.id === emotionId);
      return {
        name: em ? em.label : (emotionId.charAt(0).toUpperCase() + emotionId.slice(1)),
        value,
        color: em?.color || '#94A3B8',
      };
    })
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções
      </div>
    );
  }

  return (
    <div className="h-[380px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ left: 0, right: 15, top: 5, bottom: 5 }}>
          <XAxis
            type="number"
            tickFormatter={(v: number) => `R$${(v / 1000).toFixed(1)}k`}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="name"
            width={95}
            tick={{ fontSize: 12, fill: 'var(--text-secondary)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: any) => [formatCurrency(Number(value)), 'Valor']}
            contentStyle={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              fontSize: '13px',
            }}
            cursor={{ fill: 'var(--surface-hover)', radius: 6 }}
          />
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
