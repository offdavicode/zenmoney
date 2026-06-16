'use client';

import { Modal } from '@/components/ui/Modal';
import { type SurvivalModeReport } from '@/services/reports.service';
import { formatCurrency } from '@/utils/formatters';

interface SurvivalModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: SurvivalModeReport | null;
}

export function SurvivalModeModal({ isOpen, onClose, report }: SurvivalModeModalProps) {
  if (!report || !report.is_active || !report.trigger) return null;

  const { trigger, recommendations } = report;
  const percentage = trigger.usage_percentage;
  const remaining = trigger.limit_amount - trigger.spent_amount;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Modo Sobrevivência">
      <div className="flex flex-col gap-5">
        <div className="flex items-center gap-3">
          <div>
            <h3 className="text-base font-bold text-foreground">Modo Sobrevivência Ativo</h3>
            <p className="text-xs text-muted">
              Gatilho de ativação: {report.activation_percentage}% | Consumo atual: {Math.round(percentage)}%
            </p>
          </div>
        </div>

        {/* Barra de Progresso */}
        <div className="w-full h-3 rounded-full bg-brand-500/10 overflow-hidden">
          <div
            className="h-full rounded-full bg-brand-500 transition-all duration-700"
            style={{ width: `${Math.min(percentage, 100)}%` }}
          />
        </div>

        <div className="text-sm text-foreground bg-surface-hover border border-border p-3 rounded-xl">
          {remaining > 0 ? (
            <p>
              Você consumiu <span className="font-semibold text-brand-500 dark:text-brand-400">{formatCurrency(trigger.spent_amount)}</span> de um teto de{' '}
              <span className="font-semibold">{formatCurrency(trigger.limit_amount)}</span>. Restam{' '}
              <span className="font-bold text-brand-600 dark:text-brand-400">{formatCurrency(remaining)}</span>.
            </p>
          ) : (
            <p>
              Você excedeu seu limite de <span className="font-semibold">{formatCurrency(trigger.limit_amount)}</span> em{' '}
              <span className="font-bold text-brand-600 dark:text-brand-400">{formatCurrency(Math.abs(remaining))}</span> (total gasto:{' '}
              <span className="font-semibold">{formatCurrency(trigger.spent_amount)}</span>).
            </p>
          )}
          <p className="text-xs text-muted mt-2">
            Motivo da ativação: Limite {trigger.scope === 'global' ? 'global mensal de gastos' : `de orçamento na categoria "${trigger.category_name}"`}.
          </p>
        </div>

        {recommendations.length > 0 && (
          <div className="border-t border-border pt-4 flex flex-col gap-3">
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-bold text-secondary uppercase tracking-wider">
                Recomendações e cortes sugeridos (Não Essenciais)
              </span>
            </div>
            
            <div className="flex flex-col gap-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar">
              {recommendations.map((rec) => (
                <div key={rec.category_id} className="flex flex-col gap-1.5 p-3 rounded-xl border border-border bg-surface-hover/50 hover:bg-surface-hover transition-colors">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-bold text-foreground">{rec.category_name}</span>
                    <span className="font-semibold text-brand-500 dark:text-brand-400">{formatCurrency(rec.spent_amount)}</span>
                  </div>
                  <p className="text-xs text-secondary leading-snug">{rec.message}</p>
                  {rec.limit_amount && (
                    <div className="flex justify-between items-center text-[10px] text-muted">
                      <span>Limite: {formatCurrency(rec.limit_amount)}</span>
                      <span>Excedeu: {formatCurrency(rec.exceeded_amount)}</span>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </Modal>
  );
}
