'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { LayoutDashboard, ArrowLeftRight } from 'lucide-react';

const mobileLinks = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/lancamentos', label: 'Lançamentos', icon: ArrowLeftRight },
];

export function MobileNav() {
  const pathname = usePathname();

  return (
    <nav className="fixed bottom-0 left-0 right-0 z-50 md:hidden glass border-t border-border">
      <div className="flex items-center justify-around h-16 px-2">
        {mobileLinks.map((link) => {
          const isActive = pathname === link.href;
          return (
            <Link
              key={link.href}
              href={link.href}
              className={`flex flex-col items-center justify-center gap-1 rounded-2xl px-4 py-2 transition-all duration-200 ${isActive
                ? 'text-foreground'
                : 'text-muted hover:text-foreground'
                }`}
            >
              <link.icon size={20} strokeWidth={isActive ? 2.5 : 1.5} />
              <span className="text-[10px] font-medium">{link.label}</span>
              {isActive && (
                <span className="absolute bottom-1 h-1 w-6 rounded-full bg-brand-500 dark:bg-brand-400" />
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
