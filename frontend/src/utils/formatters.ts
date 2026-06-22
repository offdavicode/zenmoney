
export function formatCurrency(value: number | string): string {
  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num)) return String(value);
  return num.toLocaleString('pt-BR', {
    style: 'currency',
    currency: 'BRL',
  });
}


export function parseCurrencyInput(rawValue: string): number {
  const digits = rawValue.replace(/\D/g, '');
  return parseInt(digits || '0', 10) / 100;
}


export function formatCurrencyInput(value: number | string): string {
  const num = typeof value === 'number' ? value : parseFloat(value);
  if (isNaN(num)) return String(value);
  if (num === 0) return '';
  return num.toLocaleString('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}


export function formatDateBR(isoDate: string): string {
  const date = new Date(isoDate + 'T12:00:00');
  return date.toLocaleDateString('pt-BR', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
}


export function todayISO(): string {
  const now = new Date();
  const offset = now.getTimezoneOffset();
  const local = new Date(now.getTime() - offset * 60 * 1000);
  return local.toISOString().split('T')[0];
}
