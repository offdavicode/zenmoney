'use client';

import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { type VisualReportItem } from '@/services/reports.service';
import { formatCurrency } from '@/utils/formatters';

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
];

interface CategoryBarChartProps {
  data: VisualReportItem[];
}

export function CategoryBarChart({ data = [] }: CategoryBarChartProps) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    setMounted(true);
  }, []);

  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de categorias
      </div>
    );
  }

  const chartData = data.map(d => ({
    ...d,
    total_amount: Number(d.total_amount)
  }));

  return (
    <div className="h-95 w-full">
      {mounted ? (
        <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
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
              width={120}
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
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      ) : (
        <div className="h-full w-full" />
      )}
    </div>
  );
}
