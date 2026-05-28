import React, { useState } from 'react';
import { Eyebrow, Button } from './atoms.jsx';

const SAMPLE = `Hi,

We have a German couple looking for a 12-night North India heritage circuit — Delhi, Agra, Jaipur, Varanasi. They are keen on UNESCO sites, sunrise Taj, and an evening aarti on the Ganges. Luxury tier, private vehicle throughout, English-speaking guide.

Travel dates: October 2026. Two pax, double occupancy.

Please send 2–3 route options with hotels.

Best,
Thomas Müller
Fernweh Reisen GmbH`;

function ParsedPanel({ result }) {
  if (!result) return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
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
  );

  const p = result.parsed || {};
  const fields = [
    { label: 'Market', value: p.market },
    { label: 'Region', value: p.sub_region?.replace('_', ' ') },
    { label: 'Duration', value: p.duration_nights ? `${p.duration_nights[0]}–${p.duration_nights[1]} nights` : null },
    { label: 'Pax', value: p.pax },
    { label: 'Tier', value: p.hotel_tier },
    { label: 'Confidence', value: p.parser_confidence },
    { label: 'Heritage', value: p.heritage_requested ? 'Yes' : null },
    { label: 'Cities', value: p.cities?.join(', ') },
  ].filter(f => f.value != null);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <Eyebrow>Brief parsed</Eyebrow>
      <div style={{ background: 'var(--sand)', border: '1px solid var(--border)', borderRadius: 4, overflow: 'hidden' }}>
        {fields.map((f, i) => (
          <div key={i} style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: 8, padding: '7px 12px', borderBottom: i < fields.length - 1 ? '1px solid var(--rule-soft)' : 'none' }}>
            <span style={{ fontSize: 11, color: 'var(--ink-mute)', textTransform: 'uppercase', letterSpacing: '0.05em', paddingTop: 1 }}>{f.label}</span>
            <span style={{ fontSize: 12, color: 'var(--ink)', fontWeight: 500, textTransform: 'capitalize' }}>{String(f.value)}</span>
          </div>
        ))}
      </div>
      <div style={{ padding: '8px 12px', background: 'var(--meridian-tint)', borderRadius: 4, fontSize: 12, color: 'var(--meridian-deep)' }}>
        {result.itineraries?.options?.length ?? 0} routes ranked from 9,416 historical tours
      </div>
    </div>
  );
}

export default function BriefComposer({ onGenerate, loading, lastResult }) {
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
        <ParsedPanel result={lastResult} />
      </div>
    </div>
  );
}