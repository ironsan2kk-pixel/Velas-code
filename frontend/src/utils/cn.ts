/**
 * VELAS Utils - className merger
 * Объединение Tailwind классов с конфликт-резолюцией
 */

import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Объединяет классы с поддержкой Tailwind конфликтов
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
