'use client';

import { useEffect, useRef } from 'react';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function Modal({ isOpen, onClose, title, children }: ModalProps) {
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

  return (
    <div
      ref={overlayRef}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4"
      onClick={(e) => { if (e.target === overlayRef.current) onClose(); }}
    >
      
      <div className="absolute inset-0 bg-black/40 backdrop-blur-sm animate-fade-in" />

      
      <div className="relative w-full max-w-lg rounded-2xl bg-surface border border-border shadow-lg animate-slide-up max-h-[90vh] overflow-y-auto">
        
        <div className="sticky top-0 flex items-center justify-between border-b border-border bg-surface px-6 py-4 rounded-t-2xl z-10">
          <h2 className="text-lg font-semibold text-foreground">{title}</h2>
          <button
            onClick={onClose}
            className="flex h-8 w-8 items-center justify-center rounded-full text-muted hover:text-foreground hover:bg-surface-hover transition-colors"
            aria-label="Fechar"
          >
            <X size={18} />
          </button>
        </div>

        
        <div className="px-6 py-5">
          {children}
        </div>
      </div>
    </div>
  );
}
