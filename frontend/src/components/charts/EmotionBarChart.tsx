'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { type VisualReportItem } from '@/services/reports.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';

interface EmotionBarChartProps {
  data: VisualReportItem[];
}

export function EmotionBarChart({ data = [] }: EmotionBarChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de emoções
      </div>
    );
  }

  const chartData = data.map(item => {
    const em = EMOTIONS.find((e) => e.id === item.key);
    return {
      ...item,
      total_amount: Number(item.total_amount),
      color: em?.color || '#94A3B8',
    };
  });

  return (
    <div className="h-[380px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} layout="vertical" margin={{ left: 0, right: 15, top: 5, bottom: 5 }}>
          <XAxis
            type="number"
            tickFormatter={(v: number) => `R$${(v / 1000).toFixed(1)}k`}
            tick={{ fontSize: 11, fill: 'var(--text-muted)' }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="label"
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
          <Bar dataKey="total_amount" radius={[0, 6, 6, 0]} barSize={20}>
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
