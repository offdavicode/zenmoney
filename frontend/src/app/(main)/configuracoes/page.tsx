'use client';

import { useState, useRef, useEffect } from 'react';
import { ProfileSection } from '@/components/settings/ProfileSection';
import { BudgetSection } from '@/components/settings/BudgetSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { RecurrencesSection } from '@/components/settings/RecurrencesSection';
import { Button } from '@/components/ui/Button';
import { AlertCircle, CheckCircle2 } from 'lucide-react';

export default function ConfiguracoesPage() {
  const [profileState, setProfileState] = useState({ hasChanges: false, isValid: true });
  const [budgetState, setBudgetState] = useState({ hasChanges: false, isValid: true });
  const [isSaving, setIsSaving] = useState(false);
  const [globalError, setGlobalError] = useState('');
  const [globalSuccess, setGlobalSuccess] = useState('');

  const profileSaveRef = useRef<{ save: () => Promise<void>; discard: () => void } | null>(null);
  const budgetSaveRef = useRef<{ save: () => Promise<void>; discard: () => void } | null>(null);

  const hasChanges = profileState.hasChanges || budgetState.hasChanges;
  const isValid = profileState.isValid && budgetState.isValid;

  const handleSaveAll = async () => {
    setIsSaving(true);
    setGlobalError('');
    setGlobalSuccess('');

    try {
      const savePromises: Promise<void>[] = [];

      if (profileState.hasChanges && profileSaveRef.current) {
        savePromises.push(profileSaveRef.current.save());
      }

      if (budgetState.hasChanges && budgetSaveRef.current) {
        savePromises.push(budgetSaveRef.current.save());
      }

      await Promise.all(savePromises);

      setGlobalSuccess('Todas as configurações foram salvas com sucesso!');
      setTimeout(() => setGlobalSuccess(''), 4000);
    } catch (err: any) {
      console.error(err);
      setGlobalError(err.message || 'Erro ao salvar algumas configurações.');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDiscardAll = () => {
    setGlobalError('');
    setGlobalSuccess('');
    profileSaveRef.current?.discard();
    budgetSaveRef.current?.discard();
  };

  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto pb-24 relative">
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
        Configurações
      </h1>

      {globalSuccess && (
        <div className="p-4 text-sm text-[var(--accent-green)] bg-[var(--accent-green)]/10 border border-[var(--accent-green)]/20 rounded-2xl animate-fade-in flex items-center gap-3 font-semibold shadow-sm">
          <CheckCircle2 size={18} className="shrink-0" />
          <span>{globalSuccess}</span>
        </div>
      )}

      <ProfileSection onStateChange={setProfileState} saveRef={profileSaveRef} />
      <BudgetSection onStateChange={setBudgetState} saveRef={budgetSaveRef} />
      <CategoriesSection />
      <RecurrencesSection />

      
      <div 
        className={`fixed bottom-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] max-w-2xl transition-all duration-500 ease-in-out transform ${
          hasChanges 
            ? 'translate-y-0 opacity-100' 
            : 'translate-y-24 opacity-0 pointer-events-none'
        }`}
      >
        <div className="bg-surface/90 dark:bg-surface/90 backdrop-blur-md border border-border shadow-[0_10px_30px_rgba(0,0,0,0.1)] dark:shadow-[0_10px_30px_rgba(0,0,0,0.3)] rounded-2xl p-4 md:p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex flex-col gap-1">
            <span className="text-sm font-bold text-foreground">Alterações pendentes</span>
            <p className="text-xs text-secondary leading-normal">
              Você modificou alguns campos. Salve para não perder as alterações.
            </p>
            {globalError && (
              <div className="text-xs text-[var(--accent-red)] font-medium mt-1 flex items-center gap-1.5">
                <AlertCircle size={14} className="shrink-0" />
                <span>{globalError}</span>
              </div>
            )}
          </div>
          
          <div className="flex items-center gap-3 shrink-0 self-end sm:self-auto">
            <Button 
              variant="outline" 
              onClick={handleDiscardAll} 
              disabled={isSaving}
              className="text-xs font-semibold px-4 h-9 rounded-xl border-border hover:bg-surface-hover transition-colors"
            >
              Descartar
            </Button>
            <Button 
              onClick={handleSaveAll} 
              isLoading={isSaving} 
              disabled={!isValid}
              className="text-xs font-bold px-5 h-9 rounded-xl bg-primary hover:bg-primary/90 text-white shadow-lg shadow-primary/20 transition-all"
            >
              Salvar Alterações
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
