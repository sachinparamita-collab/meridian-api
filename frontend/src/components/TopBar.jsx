import React from 'react';
export default function TopBar({ onLogout }) {
  return (
    <div style={{ height: 48, display: 'flex', alignItems: 'center', padding: '0 24px', borderBottom: '1px solid var(--border)', background: 'var(--paper)', justifyContent: 'space-between', flexShrink: 0 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontFamily: 'var(--font-serif)', fontSize: 18, fontWeight: 500, color: 'var(--meridian)', letterSpacing: '-0.01em' }}>Meridian</span>
        <span style={{ fontSize: 10, fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: 'var(--ink-faint)', borderLeft: '1px solid var(--border)', paddingLeft: 10 }}>India Intelligence</span>
      </div>
      <button onClick={onLogout} style={{ background: 'transparent', border: 'none', fontSize: 12, color: 'var(--ink-mute)', cursor: 'pointer' }}>Sign out</button>
    </div>
  );
}
