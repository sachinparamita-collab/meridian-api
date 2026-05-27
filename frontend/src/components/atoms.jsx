import React from 'react';
export const MARKET_NAMES = { DEU: 'Germany', FRA: 'France', CHE: 'Switzerland', ITA: 'Italy', GBR: 'United Kingdom', USA: 'United States', AUS: 'Australia', NLD: 'Netherlands', BEL: 'Belgium', AUT: 'Austria', ESP: 'Spain', PRT: 'Portugal', POL: 'Poland', SWE: 'Sweden', NOR: 'Norway', DNK: 'Denmark', IND: 'India', SGP: 'Singapore', ARE: 'UAE', ZAF: 'South Africa', UNKNOWN: 'Unknown' };
export function marketName(code) { return MARKET_NAMES[code] || code; }
export function scoreColor(score) { const p = Math.round(score * 100); if (p >= 75) return 'var(--score-high)'; if (p >= 50) return 'var(--score-mid)'; return 'var(--score-low)'; }
export function formatScore(score) { return Math.min(Math.round(score * 100), 100); }
export const Eyebrow = ({ children, style }) => (<span style={{ fontFamily: 'var(--font-sans)', fontWeight: 500, fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-mute)', ...style }}>{children}</span>);
export const Num = ({ children, style }) => (<span style={{ fontFamily: 'var(--font-mono)', fontVariantNumeric: 'tabular-nums', ...style }}>{children}</span>);
export const TierBadge = ({ tier }) => {
  const meta = { agent: { label: 'agent', color: 'var(--tier-agent)', bg: 'var(--tier-agent-tint)' }, market: { label: 'market', color: 'var(--tier-market)', bg: 'var(--tier-market-tint)' }, global: { label: 'global', color: 'var(--tier-overall)', bg: 'var(--tier-overall-tint)' } };
  const t = meta[tier] || meta.global;
  return (<span style={{ display: 'inline-flex', alignItems: 'center', height: 19, padding: '0 8px', borderRadius: 999, fontFamily: 'var(--font-mono)', fontSize: 10, fontWeight: 500, letterSpacing: '0.04em', textTransform: 'lowercase', background: t.bg, color: t.color }}>{t.label}</span>);
};
export const Button = ({ children, variant = 'secondary', onClick, style }) => {
  const v = { primary: { background: 'var(--marigold)', color: '#fff', border: 'none' }, secondary: { background: 'var(--paper)', color: 'var(--ink)', border: '1px solid var(--border)' }, ghost: { background: 'transparent', color: 'var(--ink-mute)', border: 'none' } }[variant] || {};
  return (<button onClick={onClick} style={{ display: 'inline-flex', alignItems: 'center', gap: 6, padding: '7px 14px', borderRadius: 4, fontSize: 13, fontWeight: 500, cursor: 'pointer', ...v, ...style }}>{children}</button>);
};
