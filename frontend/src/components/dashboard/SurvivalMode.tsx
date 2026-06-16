'use client';

import { useState, useEffect } from 'react';
import { useTransactions } from '@/contexts/TransactionsContext';
import { getSurvivalModeReport, type SurvivalModeReport } from '@/services/reports.service';
import { ArrowRight, ShieldAlert } from 'lucide-react';
import { SurvivalModeModal } from './SurvivalModeModal';

interface SurvivalModeProps {
  month?: string; // Formato YYYY-MM
}

export function SurvivalMode({ month }: SurvivalModeProps) {
  const { transactions } = useTransactions();
  const [report, setReport] = useState<SurvivalModeReport | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function loadReport() {
      try {
        const data = await getSurvivalModeReport(month ? { month } : undefined);
        if (isMounted) {
          setReport(data);
        }
      } catch (err) {
        console.error('Erro ao carregar relatório do Modo Sobrevivência:', err);
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    }

    loadReport();

    return () => {
      isMounted = false;
    };
  }, [month, transactions]);

  if (isLoading || !report || !report.is_active || !report.trigger) {
    return null;
  }

  const { trigger } = report;
  const percentage = trigger.usage_percentage;

  return (
    <>
      <div
        onClick={() => setIsModalOpen(true)}
        className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 rounded-2xl border border-brand-500/20 bg-brand-500/5 px-4 py-3 hover:bg-brand-500/10 dark:hover:bg-brand-500/15 transition-all cursor-pointer animate-fade-in"
      >
        <div className="flex items-center gap-3">
          <p className="text-sm font-medium text-brand-600 dark:text-brand-400">
            <span className="font-bold">Modo Sobrevivência Ativo:</span> Você atingiu{' '}
            <span className="font-bold">{Math.round(percentage)}%</span> do seu limite{' '}
            {trigger.scope === 'global' ? 'global' : `na categoria "${trigger.category_name}"`}.
          </p>
        </div>
        <span className="text-xs font-bold text-brand-500 hover:text-brand-600 dark:hover:text-brand-400 shrink-0 sm:ml-auto">
          <div className='flex items-center justify-center'>
            <p>Ver detalhes</p>
            <ArrowRight width={18} />
          </div>
        </span>
      </div>

      <SurvivalModeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        report={report}
      />
    </>
  );
}
