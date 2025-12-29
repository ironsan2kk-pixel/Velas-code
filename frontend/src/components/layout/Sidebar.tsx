import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { cn } from '@/utils';
import { t } from '@/i18n';
import {
  LayoutDashboard,
  Wallet,
  History,
  Signal,
  Coins,
  BarChart3,
  TestTube,
  Settings,
  Bell,
  Server,
  X,
  ChevronLeft,
} from 'lucide-react';

interface NavItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navItems: NavItem[] = [
  { path: '/', label: 'nav.dashboard', icon: <LayoutDashboard className="w-5 h-5" /> },
  { path: '/positions', label: 'nav.positions', icon: <Wallet className="w-5 h-5" /> },
  { path: '/history', label: 'nav.history', icon: <History className="w-5 h-5" /> },
  { path: '/signals', label: 'nav.signals', icon: <Signal className="w-5 h-5" /> },
  { path: '/pairs', label: 'nav.pairs', icon: <Coins className="w-5 h-5" /> },
  { path: '/analytics', label: 'nav.analytics', icon: <BarChart3 className="w-5 h-5" /> },
  { path: '/backtest', label: 'nav.backtest', icon: <TestTube className="w-5 h-5" /> },
  { path: '/settings', label: 'nav.settings', icon: <Settings className="w-5 h-5" /> },
  { path: '/alerts', label: 'nav.alerts', icon: <Bell className="w-5 h-5" /> },
  { path: '/system', label: 'nav.system', icon: <Server className="w-5 h-5" /> },
];

interface SidebarProps {
  isOpen: boolean;
  onClose: () => void;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  isOpen,
  onClose,
  isCollapsed,
  onToggleCollapse,
}) => {
  const location = useLocation();

  return (
    <>
      {/* Mobile overlay */}
      {isOpen && (
        <div
          className="lg:hidden fixed inset-0 z-40 bg-black/50 backdrop-blur-sm"
          onClick={onClose}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed top-16 bottom-0 left-0 z-40',
          'bg-dark-bg-secondary border-r border-dark-border',
          'transition-all duration-300 ease-in-out',
          // Desktop
          'lg:translate-x-0',
          isCollapsed ? 'lg:w-16' : 'lg:w-60',
          // Mobile
          isOpen ? 'translate-x-0' : '-translate-x-full',
          'w-72 lg:w-auto'
        )}
      >
        {/* Mobile close button */}
        <div className="lg:hidden flex items-center justify-between p-4 border-b border-dark-border">
          <span className="font-semibold text-dark-text-primary">Меню</span>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-dark-bg-tertiary"
          >
            <X className="w-5 h-5 text-dark-text-secondary" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-3 space-y-1 overflow-y-auto h-[calc(100%-60px)] lg:h-[calc(100%-40px)]">
          {navItems.map((item) => {
            const isActive =
              item.path === '/'
                ? location.pathname === '/'
                : location.pathname.startsWith(item.path);

            return (
              <NavLink
                key={item.path}
                to={item.path}
                onClick={() => {
                  // Close mobile sidebar on navigation
                  if (window.innerWidth < 1024) {
                    onClose();
                  }
                }}
                className={cn(
                  'nav-item',
                  isActive && 'nav-item-active',
                  isCollapsed && 'lg:justify-center lg:px-0'
                )}
                title={isCollapsed ? t(item.label) : undefined}
              >
                {item.icon}
                {(!isCollapsed || window.innerWidth < 1024) && (
                  <span className="whitespace-nowrap">{t(item.label)}</span>
                )}
              </NavLink>
            );
          })}
        </nav>

        {/* Collapse toggle (desktop only) */}
        <div className="hidden lg:block absolute bottom-0 left-0 right-0 p-3 border-t border-dark-border">
          <button
            onClick={onToggleCollapse}
            className={cn(
              'w-full flex items-center gap-3 px-3 py-2 rounded-md',
              'text-dark-text-secondary hover:text-dark-text-primary hover:bg-dark-bg-tertiary',
              'transition-colors duration-200',
              isCollapsed && 'justify-center'
            )}
          >
            <ChevronLeft
              className={cn(
                'w-5 h-5 transition-transform duration-300',
                isCollapsed && 'rotate-180'
              )}
            />
            {!isCollapsed && <span>Свернуть</span>}
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
