import React, { useState } from 'react';
import { Eyebrow, Button } from './atoms.jsx';

const SAMPLE = `Hi,

We are looking for a 10 day Rajasthan trip for a couple from Germany. Interested in heritage palaces and forts. Budget is comfortable. Two pax, double room.

Could you send 2-3 options?

Thanks,
Sebastian
Wanderlust GmbH`;

export default function BriefComposer({ onGenerate, loading }) {
  const [email, setEmail] = useState(SAMPLE);
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', height: '100%', overflow: 'hidden' }}>
      <div style={{ padding: '28px 32px', display: 'flex', flexDirection: 'column', gap: 16, borderRight: '1px solid var(--border)', overflow: 'auto' }}>
        <div>
          <Eyebrow style={{ marginBottom: 8 }}>New brief</Eyebrow>
          <h1 style={{ fontFamily: 'var(--font-serif)', fontWeight: 500, fontSize: 34, letterSpacing: '-0.02em', lineHeight: 1.1, color: 'var(--ink)' }}>
            Paste an email <span style={{ fontStyle: 'italic', color: 'var(--marigold-deep)', fontWeight: 400 }}>or write a brief</span>
          </h1>
          <p style={{ marginTop: 6, color: 'var(--ink-mute)', fontSize: 13 }}>Meridian reads it and ranks routes from 9,416 historical tours.</p>
        </div>
        <div style={{ background: 'var(--paper)', border: '1px solid var(--border)', borderRadius: 4, display: 'flex', flexDirection: 'column', flex: 1, minHeight: 320 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px', borderBottom: '1px solid var(--border)', fontSize: 12, color: 'var(--ink-mute)' }}>
            <span style={{ color: 'var(--ink)', fontWeight: 500 }}>Agent brief</span>
            <span style={{ marginLeft: 'auto' }}>Draft</span>
          </div>
          <textarea value={email} onChange={e => setEmail(e.target.value)} style={{ flex: 1, border: 0, outline: 0, resize: 'none', padding: '14px 16px', fontSize: 14, lineHeight: 1.6, color: 'var(--ink)', background: 'transparent', minHeight: 280 }} />
          <div style={{ padding: '8px 14px', borderTop: '1px solid var(--border)', fontSize: 12, color: 'var(--ink-mute)' }}>{email.length} characters</div>
        </div>
        <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
          <Button variant="ghost" onClick={() => setEmail('')}>Clear</Button>
          <Button variant="primary" onClick={() => onGenerate(email)} style={{ opacity: loading ? 0.7 : 1 }}>
            {loading ? 'Generating routes…' : '✦ Generate routes'}
          </Button>
        </div>
      </div>
      <div style={{ padding: '28px 24px', display: 'flex', flexDirection: 'column', gap: 14, background: 'var(--paper)', overflow: 'auto' }}>
        <Eyebrow>How it works</Eyebrow>
        {[
          { n: '1', label: 'Parse', desc: 'Engine reads market, pax, region, duration, tier and constraints.' },
          { n: '2', label: 'Query', desc: 'Three-tier search: agent history → source market → global baseline.' },
          { n: '3', label: 'Score', desc: 'Routes scored: overlap × frequency × recency × affinity.' },
          { n: '4', label: 'Rank', desc: 'Top routes returned with hotels, activities, monuments and F&B.' },
        ].map(item => (
          <div key={item.n} style={{ display: 'grid', gridTemplateColumns: '28px 1fr', gap: 10, paddingBottom: 12, borderBottom: '1px dashed var(--rule-soft)' }}>
            <div style={{ width: 22, height: 22, borderRadius: '50%', background: 'var(--marigold-tint)', color: 'var(--marigold-deep)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 600, flexShrink: 0, marginTop: 1 }}>{item.n}</div>
            <div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--ink)', marginBottom: 2 }}>{item.label}</div>
              <div style={{ fontSize: 12, color: 'var(--ink-mute)', lineHeight: 1.5 }}>{item.desc}</div>
            </div>
          </div>
        ))}
        <div style={{ marginTop: 8, padding: 12, background: 'var(--meridian-tint)', borderRadius: 4, fontSize: 12, color: 'var(--meridian-deep)', lineHeight: 1.5 }}>
          <strong>9,416 historical tours</strong> · 241k services · DEU, FRA, CHE, ITA and 20+ markets
        </div>
      </div>
    </div>
  );
}
