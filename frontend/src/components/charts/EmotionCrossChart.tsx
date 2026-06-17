'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts';
import { type EmotionSpendingAnalysisResponse } from '@/services/reports.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';
import { AlertTriangle } from 'lucide-react';

interface EmotionCrossChartProps {
  data: EmotionSpendingAnalysisResponse | null;
}

export function EmotionCrossChart({ data }: EmotionCrossChartProps) {
  if (!data || !data.emotion_analysis) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções suficientes
      </div>
    );
  }

  const chartData = data.emotion_analysis
    .filter((d) => d.role !== 'not_informed' && d.transaction_count > 0)
    .map((item) => {
      const em = EMOTIONS.find((e) => e.id === item.emotion);
      return {
        name: item.emotion_label,
        total: Number(item.total_amount),
        average: Number(item.average_amount),
        count: item.transaction_count,
        color: em?.color || '#94A3B8',
        emotionId: item.emotion,
      };
    })
    .sort((a, b) => b.total - a.total);

  const triggers = data.emotion_analysis.filter((d) => d.is_trigger);
  const totalEmotionTxCount = chartData.reduce((acc, d) => acc + d.count, 0);
  const mostFrequent = chartData.length > 0 ? chartData.reduce((max, d) => d.count > max.count ? d : max, chartData[0]) : null;

  if (chartData.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções suficientes
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <ResponsiveContainer width="100%" height={480}>
        <BarChart data={chartData} margin={{ left: 10, right: 20 }}>
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
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} opacity={0.8} />
            ))}
          </Bar>
          <Bar dataKey="average" radius={[6, 6, 0, 0]} barSize={16}>
            {chartData.map((entry, index) => (
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
              return (
                <li key={t.emotion} className="text-sm text-secondary">
                  <span className="font-medium">{t.emotion_label}</span>: média de{' '}
                  <span className="font-semibold text-foreground">{formatCurrency(Number(t.average_amount))}</span>{' '}
                  por transação — <span className="text-[var(--accent-red)] font-medium">{t.difference_percentage}% acima</span> da média em emoções neutras.
                </li>
              );
            })}
          </ul>
        </div>
      )}
    </div>
  );
}
