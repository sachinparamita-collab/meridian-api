import React, { useState } from 'react';
import { Eyebrow, Num, TierBadge, Button } from './atoms.jsx';
import { marketName, scoreColor, formatScore } from './atoms.jsx';

function ScoreBar({ name, value, color }) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
      <span style={{ fontSize: 10, color: '#888', width: 52, flexShrink: 0 }}>{name}</span>
      <div style={{ flex: 1, height: 4, background: '#ddd', borderRadius: 2, overflow: 'hidden' }}>
        <div style={{ height: '100%', width: `${Math.round(value * 100)}%`, background: color, borderRadius: 2 }} />
      </div>
      <span style={{ fontSize: 10, color: '#555', width: 32, textAlign: 'right', flexShrink: 0, fontFamily: 'monospace' }}>{value.toFixed(2)}</span>
    </div>
  );
}

function RouteCard({ route, rank, isPrimary }) {
  const score = formatScore(route._score);
  const bd = route._breakdown || {};
  const legs = route.city_sequence.map((city, i) => ({ city, nights: route._nightly_split ? route._nightly_split[i] : null }));
  const bookings = route.booking_count;
  const pass = route.source_pass;
  const mkt = route.source_market ? marketName(route.source_market) : null;
  const months = route._recency_date ? Math.round((new Date() - new Date(route._recency_date)) / (1000*60*60*24*30.44)) : null;
  const recencyStr = months === null ? null : months < 1 ? 'this month' : months < 24 ? `${months} mo ago` : `${Math.round(months/12)} yr ago`;
  const scoreCol = score >= 75 ? '#0F6E56' : score >= 50 ? '#BA7517' : '#A32D2D';

  return (
    <div style={{ background: '#fff', border: isPrimary ? '2px solid #D97534' : '1px solid #ccc', borderRadius: 6, overflow: 'hidden', boxShadow: '0 2px 6px rgba(0,0,0,0.1)' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 14px', background: isPrimary ? '#F4E4D2' : '#f0ebe0', borderBottom: '1px solid #ddd' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: 12, color: '#888', fontFamily: 'monospace' }}>#{rank}</span>
          <TierBadge tier={pass} />
          {isPrimary && <span style={{ fontSize: 10, color: '#A8521D', fontFamily: 'monospace', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500 }}>Recommended</span>}
        </div>
        <span style={{ fontSize: 15, fontWeight: 600, color: scoreCol, fontFamily: 'monospace' }}>{score}%</span>
      </div>
      <div style={{ padding: '12px 14px 6px', display: 'flex', flexWrap: 'wrap', alignItems: 'baseline', gap: '2px 0', fontSize: 14 }}>
        {legs.map((leg, i) => (
          <React.Fragment key={i}>
            {i > 0 && <span style={{ color: '#aaa', padding: '0 5px', fontSize: 12 }}>›</span>}
            <span style={{ color: '#1A1814', fontWeight: 500 }}>{leg.city}{leg.nights != null && <span style={{ fontSize: 10, color: '#888', marginLeft: 3, fontFamily: 'monospace' }}>{leg.nights}n</span>}</span>
          </React.Fragment>
        ))}
      </div>
      <div style={{ padding: '4px 14px 10px', fontSize: 11, color: '#888', display: 'flex', gap: 5, flexWrap: 'wrap' }}>
        {pass === 'market' && mkt && <span>{mkt} market</span>}
        {pass === 'global' && <span>Global pattern</span>}
        {pass === 'agent' && <span>Agent pattern</span>}
        <span>·</span><span><strong style={{ color: '#555' }}>{bookings}</strong> bookings</span>
        {recencyStr && <><span>·</span><span>{recencyStr}</span></>}
        {route._estimated_duration && <><span>·</span><span style={{ fontFamily: 'monospace' }}>~{route._estimated_duration}n</span></>}
      </div>
      <div style={{ padding: '10px 14px', borderTop: '1px solid #eee', display: 'flex', flexDirection: 'column', gap: 5 }}>
        <ScoreBar name="Overlap"  value={bd.overlap   ?? 0} color="#185FA5" />
        <ScoreBar name="Freq"     value={bd.frequency ?? 0} color="#0F6E56" />
        <ScoreBar name="Recency"  value={bd.recency   ?? 0} color="#BA7517" />
        <ScoreBar name="Affinity" value={bd.affinity  ?? 0} color="#7F77DD" />
      </div>
    </div>
  );
}

function CityCard({ city, result }) {
  const hotel = result.hotels?.[city];
  const activities = (result.activities?.[city] || []).slice(0, 2);
  const monuments = (result.monuments?.[city] || []).slice(0, 2);
  return (
    <div style={{ background: '#fff', border: '1px solid #ddd', borderRadius: 4, overflow: 'hidden' }}>
      <div style={{ padding: '8px 14px', background: '#f0ebe0', borderBottom: '1px solid #ddd', fontSize: 13, fontWeight: 600, color: '#1A1814' }}>{city}</div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)' }}>
        {hotel && <div style={{ padding: '10px 14px', borderRight: '1px solid #eee' }}><div style={{ fontSize: 10, color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>Hotel</div><div style={{ fontSize: 12, color: '#1A1814', fontWeight: 500 }}>{hotel}</div></div>}
        {monuments.length > 0 && <div style={{ padding: '10px 14px', borderRight: '1px solid #eee' }}><div style={{ fontSize: 10, color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>Monuments</div>{monuments.map(([name], i) => <div key={i} style={{ fontSize: 12, color: '#444', marginBottom: 2 }}>{name}</div>)}</div>}
        {activities.length > 0 && <div style={{ padding: '10px 14px' }}><div style={{ fontSize: 10, color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', marginBottom: 4 }}>Activities</div>{activities.map(([name], i) => <div key={i} style={{ fontSize: 12, color: '#444', marginBottom: 2 }}>{name}</div>)}</div>}
      </div>
    </div>
  );
}

export default function RouteResults({ result, onBack, onRegenerate }) {
  const { parsed, itineraries } = result;
  const options = itineraries?.options || [];
  const caveat = itineraries?.caveat;
  const market = parsed.market ? marketName(parsed.market) : null;
  const duration = parsed.duration_nights ? (parsed.duration_nights[0] === parsed.duration_nights[1] ? `${parsed.duration_nights[0]} nights` : `${parsed.duration_nights[0]}-${parsed.duration_nights[1]} nights`) : null;
  const cities = Object.keys(result.hotels || {});

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100%' }}>
      <div style={{ padding: '20px 32px 14px', borderBottom: '1px solid #ddd', flexShrink: 0, background: '#FBF7F0' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: '#888', marginBottom: 8 }}>
          <button onClick={onBack} style={{ background: 'transparent', border: 0, color: '#888', fontSize: 12, cursor: 'pointer', padding: 0 }}>← Back</button>
          {market && <><span>·</span><span>{market}</span></>}
          {duration && <><span>·</span><span>{duration}</span></>}
          {parsed.pax && <><span>·</span><span>{parsed.pax} pax</span></>}
        </div>
        <div style={{ display: 'flex', alignItems: 'flex-end', gap: 24 }}>
          <div style={{ flex: 1 }}>
            <h1 style={{ fontFamily: 'var(--font-serif)', fontWeight: 500, fontSize: 28, letterSpacing: '-0.02em', lineHeight: 1.1, color: '#1A1814' }}>{options.length > 0 ? `${options.length} routes ranked` : 'No routes found'}</h1>
            <p style={{ marginTop: 4, color: '#888', fontSize: 13 }}>
              {parsed.sub_region && <span style={{ textTransform: 'capitalize' }}>{parsed.sub_region.replace('_', ' ')} · </span>}
              <span style={{ color: parsed.parser_confidence === 'high' ? '#0F6E56' : '#BA7517' }}>{parsed.parser_confidence} confidence</span>
              {parsed.heritage_requested && <span style={{ color: '#A8521D' }}> · heritage</span>}
            </p>
          </div>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button onClick={onRegenerate} style={{ padding: '7px 14px', borderRadius: 4, fontSize: 13, cursor: 'pointer', background: 'transparent', border: '1px solid #ccc', color: '#555' }}>↺ Regenerate</button>
            <button style={{ padding: '7px 14px', borderRadius: 4, fontSize: 13, cursor: 'pointer', background: '#D97534', border: 'none', color: '#fff', fontWeight: 500 }}>↗ Send to operator</button>
          </div>
        </div>
      </div>
      <div style={{ display: 'flex', gap: 16, padding: '8px 32px', background: '#EFE8DA', borderBottom: '1px solid #ddd', fontSize: 11, flexShrink: 0, flexWrap: 'wrap' }}>
        <span style={{ color: '#888', letterSpacing: '0.06em', textTransform: 'uppercase', fontWeight: 500, fontSize: 10 }}>Source</span>
        {['market','global','agent'].map(tier => {
          const labels = { market: (market || 'market') + ' bookings', global: 'all markets', agent: 'your agency' };
          return <span key={tier} style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}><TierBadge tier={tier} /><span>{labels[tier]}</span></span>;
        })}
      </div>
      <div style={{ padding: '18px 32px', background: '#EFE8DA', display: 'flex', flexDirection: 'column', gap: 10, minHeight: 0 }}>
        {options.length === 0 && <div style={{ padding: '40px 0', textAlign: 'center', color: '#888' }}>No historical routes matched this brief.</div>}
        {options.map((route, i) => <RouteCard key={i} route={route} rank={i+1} isPrimary={i===0} />)}
        {cities.length > 0 && (
          <div style={{ marginTop: 8 }}>
            <div style={{ fontSize: 11, fontWeight: 500, letterSpacing: '0.08em', textTransform: 'uppercase', color: '#888', marginBottom: 12, paddingTop: 8, borderTop: '1px solid #ccc' }}>City intelligence</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {cities.map(city => <CityCard key={city} city={city} result={result} />)}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}


