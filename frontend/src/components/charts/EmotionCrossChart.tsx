'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { type TransactionOut } from '@/services/transactions.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';
import { AlertTriangle } from 'lucide-react';

interface EmotionCrossChartProps {
  transactions: TransactionOut[];
}

export function EmotionCrossChart({ transactions }: EmotionCrossChartProps) {
  const expenses = transactions.filter((tx) => tx.type === 'expense');

  
  const emotionMap = new Map<string, { total: number; count: number }>();
  expenses.forEach((tx) => {
    const eid = tx.emotion || 'nao_informado';
    const current = emotionMap.get(eid) || { total: 0, count: 0 };
    emotionMap.set(eid, { total: current.total + tx.amount, count: current.count + 1 });
  });

  
  const data = Array.from(emotionMap.entries())
    .filter(([id]) => id !== 'nao_informado')
    .map(([emotionId, { total, count }]) => {
      const em = EMOTIONS.find((e) => e.id === emotionId);
      return {
        name: em ? em.label : (emotionId.charAt(0).toUpperCase() + emotionId.slice(1)),
        total,
        average: Math.round(total / count),
        count,
        color: em?.color || '#94A3B8',
        emotionId,
      };
    })
    .sort((a, b) => b.total - a.total);

  
  const neutralEmotions = ['calma', 'felicidade', 'satisfação', 'indiferença'];
  const neutralData = data.filter((d) => neutralEmotions.includes(d.emotionId));
  const neutralAvg = neutralData.length > 0
    ? neutralData.reduce((acc, d) => acc + d.average, 0) / neutralData.length
    : 0;

  
  const triggers = neutralAvg > 0
    ? data.filter((d) => !neutralEmotions.includes(d.emotionId) && d.average > neutralAvg * 1.2 && d.count >= 2)
    : [];

  const totalEmotionTxCount = data.reduce((acc, d) => acc + d.count, 0);
  const mostFrequent = data.length > 0 ? data.reduce((max, d) => d.count > max.count ? d : max, data[0]) : null;

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções suficientes
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      
      <ResponsiveContainer width="100%" height={480}>
        <BarChart data={data} margin={{ left: 10, right: 20 }}>
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tickFormatter={(v: number) => `R$${v >= 1000 ? `${(v / 1000).toFixed(1)}k` : v}`}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            formatter={(value: any, name: any) => [
              formatCurrency(Number(value)),
              name === 'total' ? 'Total' : 'Média',
            ]}
            contentStyle={{
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border-color)',
              borderRadius: '12px',
              fontSize: '13px',
            }}
            cursor={{ fill: 'var(--surface-hover)', radius: 6 }}
          />
          <Legend
            content={(props) => {
              const { payload } = props;
              return (
                <div className="flex justify-center gap-6 mt-4">
                  {payload?.map((entry: any, index: number) => {
                    const isTotal = entry.value === 'total';
                    return (
                      <div key={`item-${index}`} className="flex items-center gap-2">
                        <span 
                          className="w-3 h-3 rounded-full" 
                          style={{ 
                            backgroundColor: 'var(--text-secondary)', 
                            opacity: isTotal ? 0.8 : 0.4 
                          }} 
                        />
                        <span className="text-xs text-secondary font-medium">
                          {isTotal ? 'Total gasto' : 'Média por transação'}
                        </span>
                      </div>
                    );
                  })}
                </div>
              );
            }}
          />
          <Bar dataKey="total" radius={[6, 6, 0, 0]} barSize={24}>
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} opacity={0.8} />
            ))}
          </Bar>
          <Bar dataKey="average" radius={[6, 6, 0, 0]} barSize={16}>
            {data.map((entry, index) => (
              <Cell key={`cell-avg-${index}`} fill={entry.color} opacity={0.4} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      
      <div className="grid grid-cols-2 gap-3 border-t border-border pt-3">
        <div className="bg-surface-hover p-2.5 rounded-xl flex flex-col gap-0.5">
          <span className="text-[9px] text-muted font-bold uppercase">Sentimento frequente</span>
          <span className="text-xs text-foreground font-semibold truncate">{mostFrequent ? mostFrequent.name : 'N/A'}</span>
        </div>
        <div className="bg-surface-hover p-2.5 rounded-xl flex flex-col gap-0.5">
          <span className="text-[9px] text-muted font-bold uppercase">Lançamentos</span>
          <span className="text-xs text-foreground font-semibold truncate">{totalEmotionTxCount} transações</span>
        </div>
      </div>

      
      {triggers.length > 0 && (
        <div className="rounded-xl border border-[var(--accent-amber)]/30 bg-[var(--accent-amber)]/5 p-4">
          <div className="flex items-center gap-2 mb-2">
            <AlertTriangle size={16} className="text-[var(--accent-amber)]" />
            <h4 className="text-sm font-semibold text-[var(--accent-amber)]">Gatilhos de Gasto Detectados</h4>
          </div>
          <ul className="flex flex-col gap-1.5">
            {triggers.map((t) => {
              const pct = Math.round(((t.average - neutralAvg) / neutralAvg) * 100);
              return (
                <li key={t.emotionId} className="text-sm text-secondary">
                  <span className="font-medium">{t.name}</span>: média de{' '}
                  <span className="font-semibold text-foreground">{formatCurrency(t.average)}</span>{' '}
                  por transação — <span className="text-[var(--accent-red)] font-medium">{pct}% acima</span> da média em emoções neutras.
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
