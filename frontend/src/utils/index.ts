import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, formatDistanceToNow, parseISO } from 'date-fns';
import { ru } from 'date-fns/locale';

// ===== CSS Utilities =====

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

// ===== Number Formatting =====

export function formatNumber(
  value: number,
  options?: {
    decimals?: number;
    prefix?: string;
    suffix?: string;
    showSign?: boolean;
  }
): string {
  const { decimals = 2, prefix = '', suffix = '', showSign = false } = options || {};
  
  const sign = showSign && value > 0 ? '+' : '';
  const formatted = value.toLocaleString('ru-RU', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
  
  return `${sign}${prefix}${formatted}${suffix}`;
}

export function formatPrice(value: number, symbol?: string): string {
  // Determine decimals based on price magnitude
  let decimals = 2;
  if (symbol?.includes('BTC')) {
    decimals = value < 1 ? 6 : 2;
  } else if (value < 0.01) {
    decimals = 6;
  } else if (value < 1) {
    decimals = 4;
  } else if (value < 100) {
    decimals = 3;
  }
  
  return formatNumber(value, { decimals, prefix: '$' });
}

export function formatPercent(value: number, showSign: boolean = true): string {
  return formatNumber(value, { decimals: 2, suffix: '%', showSign });
}

export function formatVolume(value: number): string {
  if (value >= 1_000_000_000) {
    return formatNumber(value / 1_000_000_000, { decimals: 2, suffix: 'B' });
  }
  if (value >= 1_000_000) {
    return formatNumber(value / 1_000_000, { decimals: 2, suffix: 'M' });
  }
  if (value >= 1_000) {
    return formatNumber(value / 1_000, { decimals: 2, suffix: 'K' });
  }
  return formatNumber(value, { decimals: 0 });
}

export function formatCompact(value: number): string {
  return new Intl.NumberFormat('ru-RU', {
    notation: 'compact',
    compactDisplay: 'short',
    maximumFractionDigits: 2,
  }).format(value);
}

// ===== Date Formatting =====

export function formatDate(
  date: string | Date,
  formatStr: string = 'dd.MM.yyyy HH:mm'
): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return format(d, formatStr, { locale: ru });
}

export function formatRelativeTime(date: string | Date): string {
  const d = typeof date === 'string' ? parseISO(date) : date;
  return formatDistanceToNow(d, { addSuffix: true, locale: ru });
}

export function formatDuration(minutes: number): string {
  if (minutes < 60) {
    return `${Math.round(minutes)} мин`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = Math.round(minutes % 60);
  if (hours < 24) {
    return mins > 0 ? `${hours} ч ${mins} мин` : `${hours} ч`;
  }
  const days = Math.floor(hours / 24);
  const remainingHours = hours % 24;
  return remainingHours > 0 ? `${days} д ${remainingHours} ч` : `${days} д`;
}

// ===== Trading Utilities =====

export function getPnlColor(value: number): string {
  if (value > 0) return 'text-profit';
  if (value < 0) return 'text-loss';
  return 'text-dark-text-secondary';
}

export function getSideColor(side: 'LONG' | 'SHORT'): string {
  return side === 'LONG' ? 'text-long' : 'text-short';
}

export function getSideBgColor(side: 'LONG' | 'SHORT'): string {
  return side === 'LONG' ? 'bg-long' : 'bg-short';
}

export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'online':
    case 'active':
    case 'open':
    case 'filled':
      return 'text-accent-green-light';
    case 'offline':
    case 'closed':
    case 'cancelled':
      return 'text-accent-red-light';
    case 'degraded':
    case 'warning':
    case 'pending':
      return 'text-accent-yellow-light';
    case 'maintenance':
    case 'partial':
      return 'text-accent-purple-light';
    default:
      return 'text-dark-text-secondary';
  }
}

export function getVolatilityLabel(regime: 'low' | 'normal' | 'high'): string {
  switch (regime) {
    case 'low':
      return 'Низкая';
    case 'normal':
      return 'Нормальная';
    case 'high':
      return 'Высокая';
    default:
      return regime;
  }
}

export function getVolatilityColor(regime: 'low' | 'normal' | 'high'): string {
  switch (regime) {
    case 'low':
      return 'badge-blue';
    case 'normal':
      return 'badge-green';
    case 'high':
      return 'badge-red';
    default:
      return 'badge-gray';
  }
}

// ===== Symbol Utilities =====

export function getSymbolName(symbol: string): string {
  return symbol.replace('USDT', '');
}

export function getSymbolIcon(symbol: string): string {
  const base = getSymbolName(symbol).toLowerCase();
  return `https://cryptoicons.org/api/icon/${base}/32`;
}

// ===== Validation =====

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isValidNumber(value: unknown): boolean {
  return typeof value === 'number' && !isNaN(value) && isFinite(value);
}

// ===== Misc =====

export function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function debounce<T extends (...args: unknown[]) => unknown>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeoutId: ReturnType<typeof setTimeout>;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), wait);
  };
}

export function throttle<T extends (...args: unknown[]) => unknown>(
  func: T,
  limit: number
): (...args: Parameters<T>) => void {
  let inThrottle = false;
  return (...args: Parameters<T>) => {
    if (!inThrottle) {
      func(...args);
      inThrottle = true;
      setTimeout(() => {
        inThrottle = false;
      }, limit);
    }
  };
}

export function copyToClipboard(text: string): Promise<void> {
  return navigator.clipboard.writeText(text);
}

export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}
