import React, { useState } from 'react';
import { marketName, formatScore } from './atoms.jsx';

function ScoreBar({ name, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontSize: 9, color: '#888', width: 38, flexShrink: 0 }}>{name}</span>
      <div style={{ flex: 1, height: 3, background: '#ccc', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.round(value * 100)}%`, background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 9, color: '#555', width: 28, textAlign: 'right', flexShrink: 0, fontFamily: 'monospace' }}>{value.toFixed(2)}</span>
    </div>
  );
}

function RouteCard({ route, rank, isPrimary, isSelected, onClick }) {
  const score = formatScore(route._score);
  const bd = route._breakdown || {};
  const pass = route.source_pass;
  const mkt = route.source_market ? marketName(route.source_market) : null;
  const months = route._recency_date ? Math.round((new Date() - new Date(route._recency_date)) / (1000*60*60*24*30.44)) : null;
  const recencyStr = months === null ? null : months < 1 ? 'this month' : months < 24 ? `${months} mo ago` : `${Math.round(months/12)} yr ago`;
  const scoreCol = score >= 75 ? '#0F6E56' : score >= 50 ? '#BA7517' : '#A32D2D';
  const legs = route.city_sequence.map((city, i) => ({ city, nights: route._nightly_split?.[i] ?? null }));
  const tierBg = pass === 'market' ? '#FAEEDA' : pass === 'agent' ? '#E1F5EE' : '#DDE5EA';
  const tierCol = pass === 'market' ? '#854F0B' : pass === 'agent' ? '#0F6E56' : '#2E5266';
  return (
    <div onClick={onClick} style={{ display: 'grid', gridTemplateColumns: '56px 1fr', background: '#fff', border: isSelected ? '2px solid #D97534' : '1px solid #D8D0C4', borderRadius: 6, overflow: 'hidden', cursor: 'pointer', marginBottom: 6, opacity: isSelected ? 1 : 0.45, boxShadow: isSelected ? '0 2px 8px rgba(0,0,0,0.12)' : 'none', transition: 'all 120ms' }}>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '10px 4px', gap: 4, background: (isSelected || isPrimary) ? '#F4E4D2' : '#EFE8DA', borderRight: '1px solid #ddd' }}>
        <div style={{ fontSize: 22, fontWeight: 600, fontFamily: 'monospace', color: scoreCol, lineHeight: 1 }}>{score}%</div>
        <div style={{ fontSize: 10, color: '#888', fontFamily: 'monospace' }}>#{rank}</div>
        <span style={{ display: 'inline-flex', alignItems: 'center', height: 15, padding: '0 5px', borderRadius: 999, fontSize: 8, fontWeight: 500, letterSpacing: '0.04em', background: tierBg, color: tierCol, fontFamily: 'monospace' }}>{pass}</span>
      </div>
      <div style={{ padding: '8px 10px' }}>
        <div style={{ fontSize: 13, fontWeight: 500, color: '#1A1814', lineHeight: 1.5, marginBottom: 3, display: 'flex', flexWrap: 'wrap', alignItems: 'baseline' }}>
          {legs.map((leg, i) => (
            <span key={i} style={{ whiteSpace: 'nowrap', marginRight: 2 }}>
              {i > 0 && <span style={{ color: '#bbb', marginRight: 2, fontSize: 11 }}>›</span>}
              {leg.city}
              {leg.nights != null && <span style={{ fontSize: 10, color: '#A8521D', marginLeft: 2, fontFamily: 'monospace', background: '#F4E4D2', padding: '1px 4px', borderRadius: 3, fontWeight: 700 }}>{leg.nights}n</span>}
            </span>
          ))}
        </div>
        <div style={{ fontSize: 11, color: '#888', marginBottom: 7 }}>
          {pass === 'market' && mkt ? `${mkt} market` : pass === 'agent' ? 'Agent pattern' : 'Global pattern'}{' · '}<strong style={{ color: '#555' }}>{route.booking_count}</strong> bookings{recencyStr && ` · ${recencyStr}`}{route._estimated_duration && ` · ~${route._estimated_duration}n`}
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px 8px' }}>
          <ScoreBar name="Overlap"  value={bd.overlap   ?? 0} color="#185FA5" />
          <ScoreBar name="Recency"  value={bd.recency   ?? 0} color="#BA7517" />
          <ScoreBar name="Freq"     value={bd.frequency ?? 0} color="#0F6E56" />
          <ScoreBar name="Affinity" value={bd.affinity  ?? 0} color="#7F77DD" />
        </div>
      </div>
    </div>
  );
}

function DetailPanel({ route, result }) {
  if (!route) return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '200px', color: '#888', fontSize: 13 }}>
      Select a route to see details
    </div>
  );
  const legs = route.city_sequence.map((city, i) => ({ city, nights: route._nightly_split?.[i] ?? null }));
  const score = formatScore(route._score);
  const scoreCol = score >= 75 ? '#0F6E56' : score >= 50 ? '#BA7517' : '#A32D2D';
  const tierBg = route.source_pass === 'market' ? '#FAEEDA' : route.source_pass === 'agent' ? '#E1F5EE' : '#DDE5EA';
  const tierCol = route.source_pass === 'market' ? '#854F0B' : route.source_pass === 'agent' ? '#0F6E56' : '#2E5266';
  const seen = new Set();
  const uniqueLegs = legs.filter(l => { if (seen.has(l.city)) return false; seen.add(l.city); return true; });
  return (
    <div>
      <div style={{ padding: '14px 16px 10px', borderBottom: '2px solid #D4CBC0', background: '#FBF7F0', position: 'sticky', top: 0, zIndex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
          <span style={{ fontSize: 20, fontWeight: 600, fontFamily: 'monospace', color: scoreCol }}>{score}%</span>
          <span style={{ display: 'inline-flex', alignItems: 'center', height: 17, padding: '0 7px', borderRadius: 999, fontSize: 9, fontWeight: 500, letterSpacing: '0.04em', fontFamily: 'monospace', background: tierBg, color: tierCol }}>{route.source_pass}</span>
          <span style={{ fontSize: 11, color: '#888' }}>{route.booking_count} bookings · ~{route._estimated_duration}n</span>
        </div>
        <div style={{ fontSize: 13, fontWeight: 500, color: '#3D3A33', lineHeight: 1.6, display: 'flex', flexWrap: 'wrap', alignItems: 'baseline' }}>
          {legs.map((l, i) => (
            <span key={i} style={{ whiteSpace: 'nowrap', marginRight: 2 }}>
              {i > 0 && <span style={{ color: '#ccc', marginRight: 2, fontSize: 12 }}>›</span>}
              {l.city}
              {l.nights != null && <span style={{ fontSize: 11, color: '#aaa', fontFamily: 'monospace', marginLeft: 2 }}>{l.nights}n</span>}
            </span>
          ))}
        </div>
      </div>
      <div style={{ padding: '12px 16px', display: 'flex', flexDirection: 'column', gap: 10 }}>
        {uniqueLegs.map((leg, i) => {
          const city = leg.city;
          const hotel = result.hotels?.[city];
          const activities = (result.activities?.[city] || []).slice(0, 3);
          const monuments = (result.monuments?.[city] || []).slice(0, 2);
          if (!hotel && !activities.length && !monuments.length) return null;
          return (
            <div key={i} style={{ background: '#F8F5EF', border: '1px solid #D4CBC0', borderRadius: 6, overflow: 'hidden' }}>
              <div style={{ padding: '7px 12px', background: '#2E5266', borderBottom: '1px solid #1F3947', display: 'flex', alignItems: 'center', gap: 8 }}>
                <span style={{ fontSize: 12, fontWeight: 600, color: '#FFFFFF' }}>{city}</span>
                {leg.nights != null && <span style={{ fontSize: 11, color: '#DDE5EA', fontFamily: 'monospace' }}>{leg.nights}n</span>}
              </div>
              <div style={{ padding: '8px 12px', display: 'flex', flexDirection: 'column', gap: 6 }}>
                {hotel && (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 10, color: '#2E5266', width: 72, flexShrink: 0, paddingTop: 1, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>Hotels</span>
                    <span style={{ fontSize: 12, color: '#1A1814', fontWeight: 500 }}>{hotel}</span>
                  </div>
                )}
                {monuments.length > 0 && (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 10, color: '#2E5266', width: 72, flexShrink: 0, paddingTop: 1, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>Monuments</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {monuments.map(([name], j) => <span key={j} style={{ fontSize: 12, color: '#3D3A33' }}>{name}</span>)}
                    </div>
                  </div>
                )}
                {activities.length > 0 && (
                  <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                    <span style={{ fontSize: 10, color: '#2E5266', width: 72, flexShrink: 0, paddingTop: 1, letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 600 }}>Activities</span>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                      {activities.map(([name], j) => <span key={j} style={{ fontSize: 12, color: '#3D3A33' }}>{name}</span>)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default function RouteResults({ result, onBack, onRegenerate }) {
  const { parsed, itineraries } = result;
  const options = itineraries?.options || [];
  const [selectedIdx, setSelectedIdx] = useState(0);
  const selectedRoute = options[selectedIdx] || null;
  const market = parsed.market ? marketName(parsed.market) : null;
  const duration = parsed.duration_nights
    ? (parsed.duration_nights[0] === parsed.duration_nights[1]
        ? `${parsed.duration_nights[0]} nights`
        : `${parsed.duration_nights[0]}–${parsed.duration_nights[1]} nights`)
    : null;

  return (
    <div style={{ display: 'block', overflowY: 'auto', height: '100%' }}>
      <div style={{ padding: '16px 24px 12px', borderBottom: '1px solid #ddd', background: '#FBF7F0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#888', marginBottom: 6 }}>
          <button onClick={onBack} style={{ background: 'transparent', border: 0, color: '#888', fontSize: 12, cursor: 'pointer', padding: 0 }}>← Back</button>
          {market && <><span>·</span><span>{market}</span></>}
          {duration && <><span>·</span><span>{duration}</span></>}
          {parsed.pax && <><span>·</span><span>{parsed.pax} pax</span></>}
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 16 }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontFamily: 'var(--font-serif, Georgia, serif)', fontWeight: 500, fontSize: 26, letterSpacing: '-0.02em', lineHeight: 1.1, color: '#1A1814' }}>
              {options.length > 0 ? `${options.length} routes ranked` : 'No routes found'}
            </h1>
            <p style={{ marginTop: 3, color: '#888', fontSize: 12 }}>
              {parsed.sub_region && <span style={{ textTransform: 'capitalize' }}>{parsed.sub_region.replace('_', ' ')} · </span>}
              <span style={{ color: parsed.parser_confidence === 'high' ? '#0F6E56' : '#BA7517' }}>{parsed.parser_confidence} confidence</span>
              {parsed.heritage_requested && <span style={{ color: '#A8521D' }}> · heritage</span>}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button onClick={onRegenerate} style={{ padding: '6px 12px', borderRadius: 4, fontSize: 12, cursor: 'pointer', background: 'transparent', border: '1px solid #ccc', color: '#555' }}>↺ Regenerate</button>
            <button style={{ padding: '6px 12px', borderRadius: 4, fontSize: 12, cursor: 'pointer', background: '#D97534', border: 'none', color: '#fff', fontWeight: 500 }}>↗ Send to operator</button>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 6, padding: '8px 24px', background: '#F4EDE0', borderBottom: '1px solid #ddd', flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: 10, color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500, marginRight: 4 }}>Brief</span>
        {[
          { label: 'Market', value: market },
          { label: 'Duration', value: duration },
          { label: 'Pax', value: parsed.pax ? `${parsed.pax} pax` : null },
          { label: 'Tier', value: parsed.hotel_tier },
          { label: 'Region', value: parsed.sub_region?.replace('_', ' ') },
          { label: 'Confidence', value: parsed.parser_confidence },
          { label: 'Heritage', value: parsed.heritage_requested ? 'Yes' : null },
          { label: 'Cities', value: parsed.cities?.join(', ') },
        ].filter(f => f.value != null).map((f, i) => (
          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, background: '#fff', border: '1px solid #D8D0C4', borderRadius: 3, padding: '2px 7px', fontSize: 10 }}>
            <span style={{ color: '#999', textTransform: 'uppercase', letterSpacing: '0.04em' }}>{f.label}</span>
            <span style={{ color: '#3D3A33', fontWeight: 500, textTransform: 'capitalize' }}>{f.value}</span>
          </span>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 12, padding: '7px 24px', background: '#EFE8DA', borderBottom: '1px solid #ddd', fontSize: 10, flexWrap: 'wrap' }}>
        <span style={{ color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500 }}>Source</span>
        {['market','global','agent'].map(tier => {
          const labels = { market: `${market || 'market'} bookings`, global: 'all markets', agent: 'your agency' };
          const bg = tier === 'market' ? '#FAEEDA' : tier === 'agent' ? '#E1F5EE' : '#DDE5EA';
          const col = tier === 'market' ? '#854F0B' : tier === 'agent' ? '#0F6E56' : '#2E5266';
          return (
            <span key={tier} style={{ display: 'inline-flex', alignItems: 'center', gap: 5 }}>
              <span style={{ display: 'inline-flex', alignItems: 'center', height: 16, padding: '0 6px', borderRadius: 999, fontSize: 9, fontWeight: 500, letterSpacing: '0.04em', background: bg, color: col, fontFamily: 'monospace' }}>{tier}</span>
              <span style={{ color: '#73706A' }}>{labels[tier]}</span>
            </span>
          );
        })}
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', height: 'calc(100vh - 160px)' }}>
        <div style={{ padding: '14px 16px 24px', borderRight: '1px solid #ddd', overflowY: 'auto', background: '#EFE8DA' }}>
          {options.length === 0 && <div style={{ padding: '40px 0', textAlign: 'center', color: '#888', fontSize: 13 }}>No historical routes matched this brief.</div>}
          {options.map((route, i) => (
            <RouteCard key={i} route={route} rank={i+1} isPrimary={i===0} isSelected={selectedIdx===i} onClick={() => setSelectedIdx(i)} />
          ))}
        </div>
        <div style={{ background: '#FBF7F0', overflowY: 'auto' }}>
          <DetailPanel route={selectedRoute} result={result} />
        </div>
      </div>
    </div>
  );
}


