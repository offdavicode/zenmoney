'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { LayoutDashboard, ArrowLeftRight, Bell, User, LogOut } from 'lucide-react';
import { useState, useRef, useEffect, useMemo } from 'react';
import { useTransactions } from '@/contexts/TransactionsContext';
import { getSurvivalModeReport, type SurvivalModeReport } from '@/services/reports.service';
import { getBudgetAlert } from '@/services/settings.service';
import { SurvivalModeModal } from '@/components/dashboard/SurvivalModeModal';

type Notification = {
  id: string;
  message: string;
  read: boolean;
  time: string;
};

const navLinks = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/lancamentos', label: 'Lançamentos' },
];

export function Topbar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  
  const [showNotifMenu, setShowNotifMenu] = useState(false);
  const notifMenuRef = useRef<HTMLDivElement>(null);
  
  const { transactions, categories, budgetUpdatedVersion } = useTransactions();
  const [survivalReport, setSurvivalReport] = useState<SurvivalModeReport | null>(null);
  const [isSurvivalModalOpen, setIsSurvivalModalOpen] = useState(false);

  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [survivalNotifRead, setSurvivalNotifRead] = useState(false);
  const [budgetAlert, setBudgetAlert] = useState<any | null>(null);
  const [budgetAlertNotifRead, setBudgetAlertNotifRead] = useState(false);

  useEffect(() => {
    let isMounted = true;
    async function checkSurvivalMode() {
      try {
        const data = await getSurvivalModeReport();
        if (isMounted) {
          if (data.is_active && data.trigger) {
            const currentLimit = data.trigger.limit_amount;
            const currentSpent = data.trigger.spent_amount;
            
            const stored = localStorage.getItem('zenmoney_survival_last_read');
            let isNew = true;
            if (stored) {
              try {
                const parsed = JSON.parse(stored);
                if (parsed.limit === currentLimit && parsed.spent === currentSpent) {
                  isNew = false;
                }
              } catch (e) {}
            }
            
            setSurvivalNotifRead(!isNew);
          } else {
            setSurvivalNotifRead(true);
          }
          setSurvivalReport(data);
        }
      } catch (err) {
        console.error('Erro ao verificar modo sobrevivência para Topbar:', err);
      }
    }

    async function checkBudgetAlerts() {
      try {
        const data = await getBudgetAlert();
        if (isMounted) {
          if (data && data.alert) {
            const currentAlert = data.alert;
            const stored = localStorage.getItem('zenmoney_budget_alert_last_read');
            let isNew = true;
            if (stored) {
              try {
                const parsed = JSON.parse(stored);
                if (
                  parsed.threshold_percent === currentAlert.threshold_percent &&
                  parsed.scope === currentAlert.scope &&
                  parsed.category_id === currentAlert.category_id &&
                  parsed.spent_amount === currentAlert.spent_amount
                ) {
                  isNew = false;
                }
              } catch (e) {}
            }
            setBudgetAlertNotifRead(!isNew);
          } else {
            setBudgetAlertNotifRead(true);
          }
          setBudgetAlert(data?.alert || null);
        }
      } catch (err) {
        console.error('Erro ao verificar alerta crítico de orçamento para Topbar:', err);
      }
    }

    checkSurvivalMode();
    checkBudgetAlerts();

    return () => {
      isMounted = false;
    };
  }, [transactions, categories, budgetUpdatedVersion]);

  const markSurvivalAsRead = () => {
    setSurvivalNotifRead(true);
    if (survivalReport?.trigger) {
      localStorage.setItem('zenmoney_survival_last_read', JSON.stringify({
        limit: survivalReport.trigger.limit_amount,
        spent: survivalReport.trigger.spent_amount
      }));
    }
  };

  const markBudgetAlertAsRead = () => {
    setBudgetAlertNotifRead(true);
    if (budgetAlert) {
      localStorage.setItem('zenmoney_budget_alert_last_read', JSON.stringify({
        threshold_percent: budgetAlert.threshold_percent,
        scope: budgetAlert.scope,
        category_id: budgetAlert.category_id,
        spent_amount: budgetAlert.spent_amount
      }));
    }
  };

  useEffect(() => {
    if (showNotifMenu) {
      if (survivalReport?.is_active) {
        markSurvivalAsRead();
      }
      if (budgetAlert) {
        markBudgetAlertAsRead();
      }
    }
  }, [showNotifMenu, survivalReport, budgetAlert]);

  const displayNotifications = useMemo(() => {
    const list = [...notifications];
    if (survivalReport && survivalReport.is_active && survivalReport.trigger) {
      list.unshift({
        id: 'survival-mode-notif',
        message: `Atenção: Você atingiu ${Math.round(survivalReport.trigger.usage_percentage)}% do seu limite no modo sobrevivência!`,
        read: survivalNotifRead,
        time: 'Agora mesmo'
      });
    }
    if (budgetAlert) {
      list.unshift({
        id: 'budget-critical-alert-notif',
        message: budgetAlert.message,
        read: budgetAlertNotifRead,
        time: 'Alerta Crítico'
      });
    }
    return list;
  }, [notifications, survivalReport, survivalNotifRead, budgetAlert, budgetAlertNotifRead]);

  const hasUnread = displayNotifications.some(n => !n.read);

  const markAsRead = (id: string) => {
    if (id === 'survival-mode-notif') {
      markSurvivalAsRead();
      return;
    }
    if (id === 'budget-critical-alert-notif') {
      markBudgetAlertAsRead();
      return;
    }
    setNotifications(prev => prev.map(n => n.id === id ? { ...n, read: true } : n));
  };

  const handleNotificationClick = (notif: Notification) => {
    if (notif.id === 'survival-mode-notif') {
      setIsSurvivalModalOpen(true);
      setShowNotifMenu(false);
      markSurvivalAsRead();
    } else if (notif.id === 'budget-critical-alert-notif') {
      setShowNotifMenu(false);
      markBudgetAlertAsRead();
    } else {
      markAsRead(notif.id);
    }
  };

  
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (menuRef.current && !menuRef.current.contains(event.target as Node)) {
        setShowUserMenu(false);
      }
      if (notifMenuRef.current && !notifMenuRef.current.contains(event.target as Node)) {
        setShowNotifMenu(false);
      }
    }
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <header className="sticky top-0 z-50 w-full bg-white dark:bg-surface border-b border-border">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        
        <Link href="/dashboard" className="flex items-center gap-2 group">
          <img 
            src="/logo zenmoney.png" 
            alt="ZenMoney" 
            className="h-12 w-auto object-contain transition-transform group-hover:scale-[1.05]"
          />
        </Link>

        
        <nav className="hidden md:flex items-center rounded-full border border-border bg-surface p-1 gap-1">
          {navLinks.map((link) => {
            const isActive = pathname === link.href;
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2 rounded-full px-4 py-2 text-sm font-medium transition-all duration-200 ${isActive
                  ? 'bg-brand-500 text-white dark:bg-brand-600'
                  : 'text-muted hover:text-foreground hover:bg-surface-hover'
                  }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        
        <div className="flex items-center gap-2">
          
          <div className="relative" ref={notifMenuRef}>
            <button
              onClick={() => setShowNotifMenu(!showNotifMenu)}
              className="relative flex h-10 w-10 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
              aria-label="Notificações"
            >
              <Bell size={20} />
              
              {hasUnread && (
                <span className="absolute top-2 right-2.5 h-2 w-2 rounded-full bg-[var(--accent-red)] ring-2 ring-background" />
              )}
            </button>

            {showNotifMenu && (
              <div className="fixed inset-x-4 top-16 sm:absolute sm:inset-x-auto sm:right-0 sm:top-auto sm:mt-2 sm:w-80 rounded-2xl border border-border bg-surface p-2 shadow-lg animate-fade-in z-50">
                <div className="px-3 py-2 border-b border-border mb-2 flex justify-between items-center">
                  <p className="text-sm font-medium text-foreground">Notificações</p>
                  {hasUnread && (
                    <span className="text-xs text-white bg-[var(--accent-red)] px-2 py-0.5 rounded-full font-medium shadow-sm">
                      {displayNotifications.filter(n => !n.read).length} novas
                    </span>
                  )}
                </div>
                <div className="max-h-[320px] overflow-y-auto flex flex-col gap-1 pr-1 custom-scrollbar">
                  {displayNotifications.length === 0 ? (
                    <p className="text-sm text-muted text-center py-4">Nenhuma notificação.</p>
                  ) : (
                    displayNotifications.map((notif) => (
                      <div
                        key={notif.id}
                        onClick={() => handleNotificationClick(notif)}
                        onMouseEnter={() => !notif.read && markAsRead(notif.id)}
                        className={`flex flex-col gap-1 rounded-xl px-3 py-2.5 text-sm transition-all duration-300 cursor-pointer ${
                          notif.read 
                            ? 'text-secondary hover:bg-surface-hover' 
                            : 'bg-surface-hover text-foreground font-medium'
                        }`}
                      >
                        <p className="leading-snug">{notif.message}</p>
                        <span className="text-xs text-muted mt-1">{notif.time}</span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setShowUserMenu(!showUserMenu)}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-500 text-white dark:bg-brand-600 text-sm font-bold hover:opacity-80 transition-opacity"
              aria-label="Menu do usuário"
            >
              <User size={18} />
            </button>

            {showUserMenu && (
              <div className="absolute right-0 mt-2 w-56 rounded-2xl border border-border bg-surface p-2 shadow-lg animate-fade-in z-50">
                <div className="px-3 py-2 border-b border-border mb-1">
                  <p className="text-sm font-medium text-foreground">{user?.name || 'Usuário'}</p>
                  <p className="text-xs text-muted truncate">{user?.email || 'email@example.com'}</p>
                </div>
                <Link
                  href="/configuracoes"
                  onClick={() => setShowUserMenu(false)}
                  className="flex items-center gap-2 rounded-xl px-3 py-2 text-sm text-secondary hover:bg-surface-hover transition-colors"
                >
                  <User size={16} />
                  Configurações
                </Link>
                <button
                  onClick={() => { logout(); setShowUserMenu(false); }}
                  className="flex w-full items-center gap-2 rounded-xl px-3 py-2 text-sm text-[var(--accent-red)] hover:bg-surface-hover transition-colors"
                >
                  <LogOut size={16} />
                  Sair
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
      <SurvivalModeModal
        isOpen={isSurvivalModalOpen}
        onClose={() => setIsSurvivalModalOpen(false)}
        report={survivalReport}
      />
    </header>
  );
}
