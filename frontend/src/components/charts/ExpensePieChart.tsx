'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { type VisualReportItem } from '@/services/reports.service';
import { formatCurrency } from '@/utils/formatters';

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
  '#06B6D4', '#A855F7', '#F43F5E', '#22D3EE', '#94A3B8',
];

interface ExpensePieChartProps {
  data: VisualReportItem[];
}

export function ExpensePieChart({ data = [] }: ExpensePieChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de despesas
      </div>
    );
  }

  const chartData = data.map(d => ({
    ...d,
    total_amount: Number(d.total_amount)
  }));

  return (
    <div className="flex flex-col gap-5">
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
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
              {chartData.map((_, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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
        {chartData.map((entry, index) => {
          return (
            <div key={index} className="flex items-center justify-between text-xs border-b border-border/50 pb-1.5 last:border-0 last:pb-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
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
