'use client';

import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useTransactions } from '@/contexts/TransactionsContext';
import { type TransactionOut } from '@/services/transactions.service';
import { formatCurrency } from '@/utils/formatters';

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
];

interface CategoryBarChartProps {
  transactions: TransactionOut[];
}

export function CategoryBarChart({ transactions }: CategoryBarChartProps) {
  const { categories } = useTransactions();
  const expenses = transactions.filter((tx) => tx.type === 'expense');

  
  const categoryMap = new Map<number, number>();
  expenses.forEach((tx) => {
    if (tx.category_id !== null) {
      const current = categoryMap.get(tx.category_id) || 0;
      categoryMap.set(tx.category_id, current + tx.amount);
    }
  });

  
  const data = Array.from(categoryMap.entries())
    .map(([categoryId, value]) => {
      const cat = categories.find((c) => c.id === categoryId);
      return {
        name: cat ? cat.name : String(categoryId),
        value,
      };
    })
    .sort((a, b) => b.value - a.value)
    .slice(0, 10);

  if (data.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de categorias
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
          <Bar dataKey="value" radius={[0, 6, 6, 0]} barSize={20}>
            {data.map((_, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
