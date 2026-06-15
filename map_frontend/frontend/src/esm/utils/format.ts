export function formatPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function trendClass(trend: 'up' | 'down' | 'flat'): string {
  if (trend === 'up') return 'pnl-gain';
  if (trend === 'down') return 'pnl-loss';
  return 'text-[var(--am-text-3)]';
}

