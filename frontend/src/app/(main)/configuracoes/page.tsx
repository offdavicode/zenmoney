'use client';

import { ProfileSection } from '@/components/settings/ProfileSection';
import { BudgetSection } from '@/components/settings/BudgetSection';
import { CategoriesSection } from '@/components/settings/CategoriesSection';
import { RecurrencesSection } from '@/components/settings/RecurrencesSection';

export default function ConfiguracoesPage() {
  return (
    <div className="flex flex-col gap-6 max-w-6xl mx-auto pb-12">
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight">
        Configurações
      </h1>

      <ProfileSection />
      <BudgetSection />
      <CategoriesSection />
      <RecurrencesSection />
    </div>
  );
}
