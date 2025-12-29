import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/utils';
import { t } from '@/i18n';
import {
  LayoutDashboard,
  Wallet,
  BarChart3,
  Bell,
  Settings,
} from 'lucide-react';

interface BottomNavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const bottomNavItems: BottomNavItem[] = [
  { path: '/', label: 'Главная', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/positions', label: 'Позиции', icon: <Wallet className="w-5 h-5" /> },
  { path: '/analytics', label: 'Графики', icon: <BarChart3 className="w-5 h-5" /> },
  { path: '/alerts', label: 'Алерты', icon: <Bell className="w-5 h-5" /> },
  { path: '/settings', label: 'Ещё', icon: <Settings className="w-5 h-5" /> },
];

export const BottomNav: React.FC = () => {
  const location = useLocation();

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-40 bg-dark-bg-secondary border-t border-dark-border pb-safe">
      <div className="flex items-center justify-around h-16">
        {bottomNavItems.map((item) => {
          const isActive =
            item.path === '/'
              ? location.pathname === '/'
              : location.pathname.startsWith(item.path);

          return (
            <NavLink
              key={item.path}
              to={item.path}
              className={cn(
                'flex flex-col items-center justify-center gap-1 px-4 py-2',
                'text-dark-text-muted transition-colors duration-200',
                isActive && 'text-accent-blue'
              )}
            >
              <span className={cn(isActive && 'text-accent-blue')}>
                {item.icon}
              </span>
              <span className="text-xs font-medium">{item.label}</span>
            </NavLink>
          );
        })}
      </div>
    </nav>
  );
};

export default BottomNav;
