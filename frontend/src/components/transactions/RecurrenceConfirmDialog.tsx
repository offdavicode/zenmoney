'use client';

import { useEffect, useRef } from 'react';
import { AlertTriangle, Pencil } from 'lucide-react';

interface RecurrenceConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  mode: 'edit' | 'delete';
  onConfirmSingle: () => void;
  onConfirmAll: () => void;
}

export function RecurrenceConfirmDialog({
  isOpen,
  onClose,
  mode,
  onConfirmSingle,
  onConfirmAll,
}: RecurrenceConfirmDialogProps) {
  const overlayRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose();
    }
    if (isOpen) {
      document.addEventListener('keydown', handleKeyDown);
      document.body.style.overflow = 'hidden';
    }
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.body.style.overflow = '';
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const isDelete = mode === 'delete';

  const title = isDelete
    ? 'Excluir transação recorrente'
    : 'Editar transação recorrente';

  const Icon = isDelete ? AlertTriangle : Pencil;

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={(e) => {
        if (e.target === overlayRef.current) onClose();
      }}
    >
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" />

      <div className="relative w-full max-w-sm rounded-2xl bg-surface border border-border shadow-lg animate-slide-up">
        <div className="flex flex-col items-center px-6 pt-6 pb-2">
          <div
            className={`flex h-12 w-12 items-center justify-center rounded-full ${
              isDelete
                ? 'bg-[var(--accent-red)]/10 text-[var(--accent-red)]'
                : 'bg-[var(--accent-green)]/10 text-[var(--accent-green)]'
            }`}
          >
            <Icon size={24} />
          </div>

          <h2 className="mt-4 text-lg font-semibold text-foreground text-center">
            {title}
          </h2>

          <p className="mt-2 text-sm text-secondary text-center">
            Esta transação faz parte de uma recorrência. O que deseja fazer?
          </p>
        </div>

        <div className="flex flex-col gap-3 px-6 pt-4 pb-6">
          <button
            onClick={onConfirmSingle}
            className="w-full rounded-xl border border-border bg-transparent px-4 py-2.5 text-sm font-medium text-foreground hover:bg-surface-hover transition-colors"
          >
            Somente esta
          </button>

          <button
            onClick={onConfirmAll}
            className={`w-full rounded-xl px-4 py-2.5 text-sm font-medium text-white transition-colors ${
              isDelete
                ? 'bg-[var(--accent-red)] hover:bg-[var(--accent-red)]/80'
                : 'bg-[var(--accent-green)] hover:bg-[var(--accent-green)]/80'
            }`}
          >
            Esta e todas as futuras
          </button>

          <button
            onClick={onClose}
            className="mt-1 w-full text-sm text-muted hover:text-foreground transition-colors"
          >
            Cancelar
          </button>
        </div>
      </div>
    </div>
  );
}
