import React, { useState } from 'react';
import { healthCheck } from '../api.js';
export default function Login({ onLogin }) {
  const [key, setKey] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const handleSubmit = async () => {
    if (!key.trim()) return;
    setLoading(true); setError('');
    try {
      const ok = await healthCheck(key.trim());
      if (ok) { localStorage.setItem('meridian_api_key', key.trim()); onLogin(key.trim()); }
      else setError('Invalid API key. Please try again.');
    } catch { setError('Could not reach the Meridian API.'); }
    finally { setLoading(false); }
  };
  return (
    <div style={{ height: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: 'var(--bg)' }}>
      <div style={{ width: 400, padding: '48px 40px', background: 'var(--paper)', border: '1px solid var(--border)', borderRadius: 8, boxShadow: '0 16px 48px rgba(26,24,20,0.10)' }}>
        <div style={{ marginBottom: 32 }}>
          <div style={{ fontFamily: 'var(--font-serif)', fontSize: 28, fontWeight: 500, color: 'var(--meridian)', letterSpacing: '-0.02em', marginBottom: 4 }}>Meridian</div>
          <div style={{ fontSize: 13, color: 'var(--ink-mute)' }}>India travel intelligence</div>
        </div>
        <div style={{ marginBottom: 24 }}>
          <label style={{ display: 'block', fontSize: 12, fontWeight: 500, color: 'var(--ink-mute)', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 8 }}>API Key</label>
          <input type="password" value={key} onChange={e => { setKey(e.target.value); setError(''); }} onKeyDown={e => e.key === 'Enter' && handleSubmit()} placeholder="mk_..." style={{ width: '100%', padding: '10px 12px', border: `1px solid ${error ? 'var(--vermillion)' : 'var(--border)'}`, borderRadius: 4, fontSize: 14, background: 'var(--bg)', color: 'var(--ink)', outline: 'none' }} />
          {error && <div style={{ marginTop: 8, fontSize: 12, color: 'var(--vermillion)' }}>{error}</div>}
        </div>
        <button onClick={handleSubmit} style={{ width: '100%', padding: '10px 14px', background: 'var(--marigold)', color: '#fff', border: 'none', borderRadius: 4, fontSize: 13, fontWeight: 500, cursor: 'pointer' }}>
          {loading ? 'Connecting…' : 'Enter Meridian'}
        </button>
        <div style={{ marginTop: 24, fontSize: 12, color: 'var(--ink-faint)', textAlign: 'center' }}>Contact your Meridian account manager for access.</div>
      </div>
    </div>
  );
}
