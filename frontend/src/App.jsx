import React, { useState } from 'react';
import Login from './components/Login.jsx';
import TopBar from './components/TopBar.jsx';
import BriefComposer from './components/BriefComposer.jsx';
import RouteResults from './components/RouteResults.jsx';
import { recommend } from './api.js';

export default function App() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('meridian_api_key') || '');
  const [view, setView] = useState('composer');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleLogin = (key) => { setApiKey(key); };
  const handleLogout = () => { localStorage.removeItem('meridian_api_key'); setApiKey(''); setView('composer'); setResult(null); };
  const handleGenerate = async (emailText) => {
    setLoading(true); setError('');
    try { const data = await recommend(emailText, apiKey); setResult(data); setView('results'); }
    catch (e) { setError(e.message || 'Something went wrong'); }
    finally { setLoading(false); }
  };

  if (!apiKey) return <Login onLogin={handleLogin} />;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
      <TopBar onLogout={handleLogout} />
      {error && (
        <div style={{ padding: '10px 24px', background: '#F1D7D7', borderBottom: '1px solid #B83838', fontSize: 13, color: '#B83838', display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexShrink: 0 }}>
          <span>⚠ {error}</span>
          <button onClick={() => setError('')} style={{ background: 'none', border: 'none', color: '#B83838', cursor: 'pointer', fontSize: 16 }}>×</button>
        </div>
      )}
      <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
        {view === 'composer' && <BriefComposer onGenerate={handleGenerate} loading={loading} lastResult={result} />}
        {view === 'results' && result && <RouteResults result={result} onBack={() => setView('composer')} onRegenerate={() => setView('composer')} />}
      </div>
    </div>
  );
}
