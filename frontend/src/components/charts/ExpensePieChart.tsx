'use client';

import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import { useTransactions } from '@/contexts/TransactionsContext';
import { type TransactionOut } from '@/services/transactions.service';
import { formatCurrency } from '@/utils/formatters';

const COLORS = [
  '#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
  '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#84CC16',
  '#06B6D4', '#A855F7', '#F43F5E', '#22D3EE', '#94A3B8',
];

interface ExpensePieChartProps {
  transactions: TransactionOut[];
}

export function ExpensePieChart({ transactions }: ExpensePieChartProps) {
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
    .sort((a, b) => b.value - a.value);

  
  const total = data.reduce((acc, d) => acc + d.value, 0);
  const threshold = total * 0.03;
  const mainData: typeof data = [];
  let othersValue = 0;

  data.forEach((d) => {
    if (d.value < threshold) {
      othersValue += d.value;
    } else {
      mainData.push(d);
    }
  });

  if (othersValue > 0) {
    mainData.push({ name: 'Outros', value: othersValue });
  }

  if (mainData.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted text-sm">
        Sem dados de despesas
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={mainData}
              cx="50%"
              cy="50%"
              innerRadius={65}
              outerRadius={95}
              paddingAngle={3}
              dataKey="value"
              stroke="none"
            >
              {mainData.map((_, index) => (
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
        {mainData.map((entry, index) => {
          const pct = total > 0 ? ((entry.value / total) * 100).toFixed(0) : 0;
          return (
            <div key={index} className="flex items-center justify-between text-xs border-b border-border/50 pb-1.5 last:border-0 last:pb-0">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: COLORS[index % COLORS.length] }} />
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
