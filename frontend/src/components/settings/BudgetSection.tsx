'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Plus, Trash2, Edit2 } from 'lucide-react';
import { formatCurrency, formatCurrencyInput, parseCurrencyInput } from '@/utils/formatters';
import { getBudget, updateBudget, BudgetOut, CategoryLimitInput, getSurvivalModeConfig, updateSurvivalModeConfig } from '@/services/settings.service';
import { useTransactions } from '@/contexts/TransactionsContext';

interface BudgetSectionProps {
  onStateChange: (state: { hasChanges: boolean; isValid: boolean }) => void;
  saveRef: React.MutableRefObject<{ save: () => Promise<void>; discard: () => void } | null>;
}

export function BudgetSection({ onStateChange, saveRef }: BudgetSectionProps) {
  const { categories, notifyBudgetUpdated } = useTransactions();
  const [budget, setBudget] = useState<BudgetOut | null>(null);
  const [globalLimit, setGlobalLimit] = useState(0);
  const [globalLimitRaw, setGlobalLimitRaw] = useState('');
  
  const [isSaving, setIsSaving] = useState(false);
  const [msg, setMsg] = useState('');
  
  const [showAddLimit, setShowAddLimit] = useState(false);
  const [selectedCatId, setSelectedCatId] = useState<number | ''>('');
  const [newCatLimitRaw, setNewCatLimitRaw] = useState('');
  
  const [survivalPercent, setSurvivalPercent] = useState<number>(80);
  const [survivalMsg, setSurvivalMsg] = useState('');

  const [initialGlobalLimit, setInitialGlobalLimit] = useState(0);
  const [initialSurvivalPercent, setInitialSurvivalPercent] = useState(80);

  const loadData = async () => {
    try {
      const [budgetData, survivalData] = await Promise.all([
        getBudget(),
        getSurvivalModeConfig()
      ]);
      setBudget(budgetData);
      
      const valPercent = survivalData.activation_percentage;
      setSurvivalPercent(valPercent);
      setInitialSurvivalPercent(valPercent);
      
      const gl = budgetData.global_limit?.limit_amount || 0;
      setGlobalLimit(gl);
      setGlobalLimitRaw(formatCurrencyInput(gl));
      setInitialGlobalLimit(gl);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const hasChanges = globalLimit !== initialGlobalLimit || survivalPercent !== initialSurvivalPercent;
  const isGlobalLimitValid = globalLimit > 0;
  const isSurvivalPercentValid = survivalPercent >= 50 && survivalPercent <= 90;
  const isValid = (!hasChanges) || (isGlobalLimitValid && isSurvivalPercentValid);

  useEffect(() => {
    onStateChange({ hasChanges, isValid });
  }, [hasChanges, isValid, onStateChange]);

  useEffect(() => {
    saveRef.current = {
      save: async () => {
        setMsg('');
        setSurvivalMsg('');
        
        let errorMessages: string[] = [];
        let updatedAny = false;

        if (globalLimit !== initialGlobalLimit) {
          if (globalLimit <= 0) {
            const err = 'O limite global deve ser maior que zero.';
            setMsg(err);
            errorMessages.push(err);
          } else {
            try {
              await updateBudget({ global_limit: globalLimit });
              setMsg('Limite global atualizado!');
              updatedAny = true;
            } catch (e: any) {
              const err = e.message || 'Erro ao salvar limite global.';
              setMsg(err);
              errorMessages.push(err);
            }
          }
        }

        if (survivalPercent !== initialSurvivalPercent) {
          if (survivalPercent < 50 || survivalPercent > 90) {
            const err = 'O gatilho do modo sobrevivência deve ser entre 50% e 90%.';
            setSurvivalMsg(err);
            errorMessages.push(err);
          } else {
            try {
              await updateSurvivalModeConfig({ activation_percentage: survivalPercent });
              setSurvivalMsg('Gatilho do Modo Sobrevivência atualizado!');
              updatedAny = true;
            } catch (e: any) {
              const err = e.message || 'Erro ao salvar gatilho do modo sobrevivência.';
              setSurvivalMsg(err);
              errorMessages.push(err);
            }
          }
        }

        if (errorMessages.length > 0) {
          throw new Error(errorMessages.join(' | '));
        }

        if (updatedAny) {
          await loadData();
          notifyBudgetUpdated();
        }
      },
      discard: () => {
        setMsg('');
        setSurvivalMsg('');
        setGlobalLimit(initialGlobalLimit);
        setGlobalLimitRaw(formatCurrencyInput(initialGlobalLimit));
        setSurvivalPercent(initialSurvivalPercent);
      }
    };
  }, [globalLimit, initialGlobalLimit, survivalPercent, initialSurvivalPercent, notifyBudgetUpdated]);

  const handleGlobalLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const parsed = parseCurrencyInput(e.target.value);
    setGlobalLimit(parsed);
    setGlobalLimitRaw(formatCurrencyInput(parsed));
  };

  const handleAddCategoryLimit = async () => {
    if (!selectedCatId || !newCatLimitRaw) return;
    
    setIsSaving(true);
    const amount = parseCurrencyInput(newCatLimitRaw);
    try {
      const currentLimits: CategoryLimitInput[] = budget?.category_limits.map(cl => ({
        category_id: cl.category_id as number,
        amount: cl.limit_amount
      })) || [];
      
      const idx = currentLimits.findIndex(c => c.category_id === Number(selectedCatId));
      if (idx >= 0) {
        currentLimits[idx].amount = amount;
      } else {
        currentLimits.push({ category_id: Number(selectedCatId), amount });
      }

      await updateBudget({ category_limits: currentLimits });
      setShowAddLimit(false);
      setSelectedCatId('');
      setNewCatLimitRaw('');
      await loadData();
      notifyBudgetUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCategoryLimit = async (categoryId: number) => {
    setIsSaving(true);
    try {
      const currentLimits: CategoryLimitInput[] = budget?.category_limits.map(cl => ({
        category_id: cl.category_id as number,
        amount: cl.limit_amount
      })) || [];
      
      const newLimits = currentLimits.filter(c => c.category_id !== categoryId);
      
      await updateBudget({ category_limits: newLimits });
      await loadData();
      notifyBudgetUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Card>
      <div className="flex items-center justify-between mb-4">
        <div>
          <h2 className="text-lg font-semibold text-foreground">Teto de Gastos</h2>
          <p className="text-sm text-muted">Defina seus limites financeiros</p>
        </div>
      </div>
      
      <div className="flex flex-col gap-6">
        <div className="flex w-full flex-col gap-2">
          <label className="text-sm font-medium text-foreground">Limite Global Mensal</label>
          <div className="relative max-w-sm">
            <span className="absolute left-3 top-1/2 -translate-y-1/2 text-sm font-medium text-muted">
              R$
            </span>
            <input
              type="text"
              inputMode="numeric"
              value={globalLimitRaw}
              onChange={handleGlobalLimitChange}
              className="flex h-10 w-full rounded-md border border-border bg-surface pl-10 pr-3 py-2 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            />
          </div>
          {globalLimit <= 0 && (
            <span className="text-xs text-[var(--accent-red)]">O limite deve ser maior que zero.</span>
          )}
          {msg && <span className="text-xs text-[var(--accent-green)]">{msg}</span>}
        </div>

        <div className="border-t border-border pt-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-medium text-foreground">Limites por Categoria</h3>
            <Button variant="ghost" size="sm" className="h-8 gap-1 text-brand-600" onClick={() => setShowAddLimit(!showAddLimit)}>
              <Plus size={14} /> Adicionar
            </Button>
          </div>

          {showAddLimit && (
            <div className="flex flex-col sm:flex-row gap-2 mb-4 p-3 bg-surface-hover rounded-lg border border-border items-end animate-fade-in">
              <div className="flex-1 w-full">
                <label className="text-xs font-medium text-muted mb-1 block">Categoria</label>
                <select 
                  className="w-full h-9 rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  value={selectedCatId}
                  onChange={(e) => setSelectedCatId(Number(e.target.value))}
                >
                  <option value="" disabled>Selecione uma categoria</option>
                  {categories.filter(c => c.type === 'expense').map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div className="flex-1 w-full">
                <label className="text-xs font-medium text-muted mb-1 block">Limite (R$)</label>
                <input
                  type="text"
                  inputMode="numeric"
                  value={newCatLimitRaw}
                  onChange={(e) => setNewCatLimitRaw(formatCurrencyInput(parseCurrencyInput(e.target.value)))}
                  className="w-full h-9 rounded-md border border-border bg-surface px-3 py-1 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                  placeholder="0,00"
                />
              </div>
              <Button size="sm" className="h-9 w-full sm:w-auto" onClick={handleAddCategoryLimit} isLoading={isSaving} disabled={!selectedCatId || !newCatLimitRaw}>
                Salvar
              </Button>
            </div>
          )}
          
          <div className="flex flex-col gap-3">
            {!budget?.category_limits || budget.category_limits.length === 0 ? (
               <p className="text-sm text-muted">Nenhum limite por categoria definido.</p>
            ) : (
              budget.category_limits.map((catLimit) => {
                const catInfo = categories.find(c => c.id === catLimit.category_id);
                return (
                  <div key={catLimit.category_id} className="flex items-center justify-between p-3 rounded-lg bg-surface-hover">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">{catLimit.category_name}</span>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-semibold">{formatCurrency(catLimit.limit_amount)}</span>
                      <button 
                        onClick={() => {
                          setSelectedCatId(catLimit.category_id as number);
                          setNewCatLimitRaw(formatCurrencyInput(catLimit.limit_amount));
                          setShowAddLimit(true);
                        }}
                        className="text-muted hover:text-primary disabled:opacity-50"
                        disabled={isSaving}
                        title="Editar limite"
                      >
                        <Edit2 size={16} />
                      </button>
                      <button 
                        onClick={() => handleDeleteCategoryLimit(catLimit.category_id as number)}
                        className="text-muted hover:text-[var(--accent-red)] disabled:opacity-50"
                        disabled={isSaving}
                        title="Excluir limite"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        <div className="border-t border-border pt-4 flex w-full flex-col gap-2">
          <h3 className="text-sm font-medium text-foreground">Modo Sobrevivência</h3>
          <p className="text-xs text-muted font-medium mt-0.5">
            Defina a porcentagem de consumo do limite (global ou por categoria) que ativa o Modo Sobrevivência.
          </p>
          <div className="relative max-w-sm mt-2">
            <input
              type="number"
              min={50}
              max={90}
              value={survivalPercent || ''}
              onChange={(e) => setSurvivalPercent(Number(e.target.value))}
              className="flex h-10 w-full rounded-md border border-border bg-surface pl-3 pr-8 py-2 text-sm font-semibold text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
            />
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-sm font-medium text-muted">
              %
            </span>
          </div>
          {survivalPercent < 50 || survivalPercent > 90 ? (
            <span className="text-xs text-[var(--accent-red)]">O gatilho deve ser entre 50% e 90%.</span>
          ) : null}
          {survivalMsg && <span className="text-xs text-[var(--accent-green)] font-semibold">{survivalMsg}</span>}
        </div>
      </div>
    </Card>
  );
}
