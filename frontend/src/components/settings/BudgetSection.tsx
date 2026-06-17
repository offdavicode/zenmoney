'use client';

import { useState, useEffect } from 'react';
import { Card } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Plus, Trash2 } from 'lucide-react';
import { formatCurrency, formatCurrencyInput, parseCurrencyInput } from '@/utils/formatters';
import { getBudget, updateBudget, BudgetOut, CategoryLimitInput, getSurvivalModeConfig, updateSurvivalModeConfig } from '@/services/settings.service';
import { listCategories, CategoryOut } from '@/services/categories.service';
import { useTransactions } from '@/contexts/TransactionsContext';

export function BudgetSection() {
  const { notifyBudgetUpdated } = useTransactions();
  const [budget, setBudget] = useState<BudgetOut | null>(null);
  const [globalLimit, setGlobalLimit] = useState(0);
  const [globalLimitRaw, setGlobalLimitRaw] = useState('');
  const [categories, setCategories] = useState<CategoryOut[]>([]);
  
  const [isSaving, setIsSaving] = useState(false);
  const [msg, setMsg] = useState('');
  
  const [showAddLimit, setShowAddLimit] = useState(false);
  const [selectedCatId, setSelectedCatId] = useState<number | ''>('');
  const [newCatLimitRaw, setNewCatLimitRaw] = useState('');
  
  const [survivalPercent, setSurvivalPercent] = useState<number>(80);
  const [survivalMsg, setSurvivalMsg] = useState('');
  const [isSavingSurvival, setIsSavingSurvival] = useState(false);

  const loadData = async () => {
    try {
      const [budgetData, catData, survivalData] = await Promise.all([
        getBudget(),
        listCategories(),
        getSurvivalModeConfig()
      ]);
      setBudget(budgetData);
      setCategories(catData);
      setSurvivalPercent(survivalData.activation_percentage);
      
      const gl = budgetData.global_limit?.limit_amount || 0;
      setGlobalLimit(gl);
      setGlobalLimitRaw(formatCurrencyInput(gl));
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleGlobalLimitChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const parsed = parseCurrencyInput(e.target.value);
    setGlobalLimit(parsed);
    setGlobalLimitRaw(formatCurrencyInput(parsed));
  };

  const handleSaveGlobalLimit = async () => {
    setIsSaving(true);
    try {
      await updateBudget({ global_limit: globalLimit });
      setMsg('Limite global atualizado!');
      setTimeout(() => setMsg(''), 3000);
      await loadData();
      notifyBudgetUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSaving(false);
    }
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

  const handleSaveSurvivalConfig = async () => {
    if (survivalPercent < 50 || survivalPercent > 90) return;
    setIsSavingSurvival(true);
    try {
      await updateSurvivalModeConfig({ activation_percentage: survivalPercent });
      setSurvivalMsg('Gatilho do Modo Sobrevivência atualizado!');
      setTimeout(() => setSurvivalMsg(''), 3000);
      await loadData();
      notifyBudgetUpdated();
    } catch (e) {
      console.error(e);
    } finally {
      setIsSavingSurvival(false);
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
          <div className="flex gap-2 items-center">
            <div className="relative max-w-sm flex-1">
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
            <Button onClick={handleSaveGlobalLimit} isLoading={isSaving} disabled={globalLimit <= 0}>
              Salvar Limite
            </Button>
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
                        onClick={() => handleDeleteCategoryLimit(catLimit.category_id as number)}
                        className="text-muted hover:text-[var(--accent-red)] disabled:opacity-50"
                        disabled={isSaving}
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
          <div className="flex gap-2 items-center mt-2">
            <div className="relative max-w-sm flex-1">
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
            <Button onClick={handleSaveSurvivalConfig} isLoading={isSavingSurvival} disabled={survivalPercent < 50 || survivalPercent > 90}>
              Salvar Gatilho
            </Button>
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
