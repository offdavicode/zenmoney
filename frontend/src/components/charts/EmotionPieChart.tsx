'use client';

import { useState, useEffect } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { type VisualReportItem } from '@/services/reports.service';
import { EMOTIONS } from '@/utils/constants';
import { formatCurrency } from '@/utils/formatters';

interface EmotionPieChartProps {
  data: VisualReportItem[];
}

export function EmotionPieChart({ data = [] }: EmotionPieChartProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

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
    <div className="flex flex-col gap-5 flex-1 justify-between">
      <div className="h-62.5 w-full shrink-0">
        {mounted ? (
          <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                innerRadius={65}
                outerRadius={95}
                paddingAngle={3}
                dataKey="total_amount"
                stroke="none"
              >
                {chartData.map((entry, index) => (
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
        ) : (
          <div className="h-full w-full" />
        )}
      </div>

      <div className="flex flex-col gap-2 flex-1 overflow-y-auto pr-1">
        {chartData.map((entry, index) => {
          return (
            <div key={index} className="flex items-center justify-between text-xs border-b border-border/50 pb-1.5 last:border-0 last:pb-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: entry.color }} />
                <span className="text-secondary font-medium">{entry.label}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-semibold text-foreground">{formatCurrency(entry.total_amount)}</span>
                <span className="text-muted">({entry.percentage}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
