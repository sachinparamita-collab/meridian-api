"""
B27 — Historical Query Prototype  v0.6.0_ThreeTier
====================================================
v0.6.0_ThreeTier (Thu 14 May 2026) — Architecture refactor: true three-tier model

  Core principle enforced: Agent / Source Market / Global — exactly three tiers.
  Regions / States / Cities are search parameters within each tier, not tiers.

  Changes:
  - query_pass() gains geography_cities param. When set (global pass only),
    runs two sub-queries internally and merges:
      A: top-100 by global volume (high-volume routes — Golden Triangle etc.)
      B: top-100 containing ≥1 city from geography_cities (geographically
         relevant routes that may not crack global top-100)
    Guarantees global always contains both popular AND geography-relevant routes.
    Agent and market passes always call with geography_cities=None (unchanged).

  - Pass 4 (region-scoped query) removed. It was a pseudo-tier masquerading
    as a search parameter workaround. Its function is now inside query_pass().

  - Pass 5 (global fallback) removed. It was a band-aid for the same problem.
    With geography-aware query_pass(), global always returns something relevant.

  - Merge block reduced from 4 sources to 3 (agent, market, global). Clean.

  - geography_boost uses SUB_REGION_TO_CITIES[sub_region] when sub_region is
    active (richer than parent region — e.g. rajasthan has 19 cities including
    Ranthambore, north_india parent only has 9 and omits it). Falls back to
    parent region expansion when no sub_region. This ensures Sub-query B always
    pulls geographically relevant sequences into the global candidate pool.

v0.5.9_GlobalFallback (Thu 14 May 2026) — Pass 5 global fallback (superseded)

  Principle enforced: "Agent → Market → Global always has something."
  When sub_region is active and all four passes return zero candidates
  (e.g. ITA + Rajasthan — agent has no Rajasthan history, global top-200
  is dominated by Golden Triangle which gets filtered by sub-region overlap),
  Pass 5 re-runs global using the full parent region city set (no sub-region
  restriction). Guarantees ranked routes section is never empty.

  Fallback candidates are scored normally — they rank lower than sub-region
  matches because their overlap against the sub-region city set is partial,
  which is the correct signal. The ranked table always shows, with scores
  reflecting genuine fit.

v0.5.8_SubRegion (Thu 14 May 2026) — Sub-region overlap scoring + gateway cities

  Problem solved: when an agent emails "Rajasthan 10 nights", the engine
  detected north_india and expanded relevant_cities to 50+ cities including
  Delhi, Shimla, Agra, Amritsar. A Golden Triangle + Shimla route scored
  high on overlap (Delhi, Agra, Jaipur all in north_india set) and ranked
  above pure Rajasthan routes.

  Fix: when intent['sub_region'] is set (e.g. 'rajasthan'), historical_query
  uses SUB_REGION_TO_CITIES['rajasthan'] for overlap scoring — 19 Rajasthan
  cities. Gateway cities (Delhi, Mumbai, etc.) are excluded from the overlap
  set and treated as neutral — present in a sequence does not count toward
  or against sub-region overlap. Golden Triangle earns its rank by how many
  Rajasthan cities it contains, not by volume alone.

  Changes:
  - GATEWAY_CITIES: 13-city set of major entry/transit hubs — neutral in overlap
  - SUB_REGION_TO_CITIES: 15 sub-regions from rajasthan to andaman
  - get_overlap_cities(): returns (relevant_cities, gateway_set) — sub-region
    aware, gateway-exclusive
  - relevance_filter(): new gateway_cities param — excludes gateways from
    overlap count in all four passes (agent/market/global/region)
  - historical_query(): reads intent['sub_region'], calls get_overlap_cities(),
    passes gateway_cities to all relevance_filter calls

v0.5.7_BL2γ (Thu 14 May 2026) — BL2-γ: city-set (B) fallback in agent-pass scoring

  Problem solved: sequence-diverse agents (e.g. Asia365 — 111 tours, 24+ distinct
  literal sequences, max per-sequence count ≤2) returned zero agent-pass candidates
  above the cascade threshold. Their agent signal was real but fragmented across many
  literal sequences, so A-driven frequency factor topped out at ~0.32 (log(3)/log(31)),
  losing to high-volume global options even with 3.0× affinity boost.

  BL0 Q-D (Mechanism 1): A is primary; if A_freq < BL1_A_FREQ_MIN_THRESHOLD (5),
  fall to B (sequence-agnostic city-set count).

  BL1 implemented A→B in compute_signature_route() (the 40%-concentration test).
  BL2-γ extends the same fallback into score_candidate() — the frequency factor
  and label generation — so B-driven frequency lifts the score when A is thin.

  Changes in this version (C24–C27):

  C24: New helper _compute_agent_b_counts(db_path, account_code, region_cities)
       Queries agent's multi-city corpus (≥2 cities, last 24mo), groups by
       frozenset of cities (sequence-agnostic), sums counts per city-set,
       and returns {frozenset → int}.
       Region filter: only sets with ≥1 city overlapping the region are included.

  C25: historical_query() — after agent_results are gathered, compute B-counts
       for the agent, then for each agent-pass candidate:
         - compute its city-set key = frozenset(c['city_sequence'])
         - if agent_b_count[key] >= A_freq AND A_freq < BL1_A_FREQ_MIN_THRESHOLD:
             attach c['agent_b_count'] = b_freq and c['_b_driven'] = True
       Candidates where A is strong (A_freq ≥ 5) are left unchanged.

  C26: score_candidate() — frequency factor now checks for _b_driven flag:
         if _b_driven: use agent_b_count for frequency calculation
         else:          use booking_count (unchanged from v0.5.5)
       New breakdown key 'freq_source': 'B (city-set)' | 'A (literal)'.

  C27: build_label() — when _b_driven is True, uses "city-set match" phrasing:
       "[Asia365's city-set match · 7 of 111 bookings · last 3 mo ago]"
       vs the default "[Asia365's pattern · N bookings · last N mo ago]"

  BL2-β recency weights (v0.5.6_BL2β, 12 May 2026) retained — 1.0/0.8/0.5/0×.
  All test cases that passed in BL2-β must continue to pass.

v0.5.5_BL1 (Fri 08 May 2026 evening) — BL0/BL1: signature route detection
  C20: New compute_signature_route() implements BL0 Section 10's signature-
       route trigger. Fires when the agent's top route (by literal sequence
       count, A) covers ≥40% of their multi-city, last-24-month corpus AND
       that route's cities majority-overlap (≥50%) the requested region.
       When fired, relabels the matching candidate as
         "[Your literal pattern · N bookings · X% concentration]"  (A drives)
         "[Your city-set match · N bookings · X% concentration]"   (B drives)
       and forces it to position 0 in the envelope.
  C21: Type 3 (explicit route) suppression — checks intent.explicit_itinerary
       and intent._input_mode against ('TOURLANE', 'CSV', 'PDF'). BL1 only
       fires for Type 1 (region-only) and Type 2 (constrained).
  C22: A-primary, B-fallback (BL0 Q-D, Mechanism 1) — if agent's top literal
       sequence count < 5, fall to sequence-agnostic city-set count.
  C23: New module-level constants block for BL1 thresholds (concentration,
       agent signal, recency cutoff, region-match, A_freq fallback).

  DEFERRED to BL2 (out of scope for BL1):
    - Reading 2 cascade with reserved per-tier slots (10-slot envelope rule)
    - Recency decay update from 1.0/0.7/0.4/0.1 → BL0's 1.0/0.8/0.5/0×
    - B-driven frequency ranking within the agent tier
    - Q-K "agent has no history in this region" banner
    - BL3 distinctive-cities side banner (separate ticket)

v0.5.4b (Tue 06 May 2026 evening) — group-booking dedup hotfix
  C19: services query now uses SELECT DISTINCT (city_name, check_in, check_out).
       Some master.db bookings store one accommodation row per pax per night
       (e.g. an 18-pax German group tour produced 216 rows for a 12-stay
       itinerary, all exact duplicates). The non-DISTINCT SUM inflated
       _nightly_split by the pax factor (~18×). DISTINCT collapses the rows
       back to unique stays. Audley-style 1-2 pax bookings are unaffected
       (no duplicates to collapse).

v0.5.4 (Tue 06 May 2026 evening) — B27-UX Phase 5+: nightly_split + percentage display
  C16: Per-option `nightly_split` sourced from the most-recent matching booking's
       accommodation services. Aggregated per city via tours.file_code → services
       join (record_type='Accommodation', summed nights from check_in/check_out).
       Length aligned to len(city_sequence). Falls back to even distribution
       (1 night each + 2 spare) if services data unavailable.
  C17: `_estimated_duration` = sum(_nightly_split). Replaces the prior
       len(sequence)+2 heuristic at the option level.
  C18: print_options renders cities with inline nights ("Delhi 1n → Agra 1n").
       WRAP_AT lowered from 6 to 5 to absorb the wider per-item width.
       Score column displays as percentage (round(score×100)+"%") instead of
       0.XXX decimal. Threshold language unchanged in caveat banner.

v0.5.3 (Tue 06 May 2026 afternoon) — B27-UX Phase 1+2: locked contract + Colab rendering
  C13: assemble_options now returns a result envelope
       {options: list, caveat: str|None, diagnostic: dict}
       instead of a bare list. Caveat carries below-threshold messaging,
       diagnostic carries internal counts + reason for the empty/caveat
       cases. One contract, four future surface renderings.
  C14: Single ranked list — no more ★ Option vs ref binary.
       TOP_N_OPTIONS raised from 7 to 10. REFERENCE_FLOOR dropped to 0.0
       (we keep any non-zero score). Score column is the consultant's
       confidence signal; promote/ref labels gone.
  C15: print_options renders three layouts:
       (a) Normal — at least one option scores ≥ 0.50 → top 10, no caveat
       (b) Caveat — none ≥ 0.50 but ≥ 1 scored > 0 → top 3 + caveat banner
       (c) Empty/diagnostic — nothing scored → diagnostic-only message
       Status column dropped. O/F/R/A/D column dropped from default
       (still on `_breakdown` for surfaces that want to expand).

v0.5.2 (Tue 06 May 2026 morning) — B27-AGENCY-LOOKUP fix
  C11: historical_query() now reads engine-canonical keys
       (agency_account_code, source_market) with fallback to legacy
       (account_code, market) so standalone test cases still work.
  C12: assemble_options() sources agent_name from intent['agency_name']
       when not passed as a parameter — supports recommend() integration.

v0.5.1c (Mon 04 May 2026)
  C6: REGION_TO_CITIES expanded to cover all engine-emitted regions
       (added central_india, east_india, west_india, northeast_india, himalaya).
  C7: Added Pass 4 — region-scoped SQL query for region-only requests.
  C8: score_candidate normalises duration tuples internally (handles
       (lo, hi) tuples from PNR-derived date ranges).
  C9: Prefix-dedup in assemble_options on near-identical sequences,
       using date-attribute equality (year/month) not string slicing.
  C10: print_options shows FULL city sequence — wraps to continuation
       line after city #6 instead of "(+N)" truncation.

v0.5 (Mon 04 May 2026 morning)
  C4: Frequency log-scaled, saturates at ~30 (was linear, capped at 10).
  C5: Affinity tiered on agent_count/booking_count ratio (was absolute).

v0.4 (legacy)
  C1: All three passes always run.
  C2: Merge takes MAX(booking_count) across passes.
  C3: Cap raw candidates at 50 before scoring.

Run from Colab:
    !python3 /content/historical_query.py
"""

import sqlite3
import math
from datetime import datetime, date


import os as _os
DB_PATH = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'master_v2.db')

MIN_SEQ_LEN = 3
MAX_SEQ_LEN = 12
OVERLAP_RATIO_FLOOR = 0.5
PROMOTE_THRESHOLD  = 0.50    # at-least-one above this → no caveat banner
WILDLIFE_PROMOTE_THRESHOLD = 0.10    # lower bar for wildlife zones — thin data expected
REFERENCE_FLOOR    = 0.0     # v0.5.3 C14: keep any non-zero score; consultant judges via score column
TOP_N_OPTIONS      = 10      # v0.5.3 C14: was 7
MIN_OPTIONS_DISPLAY = 3      # v0.5.3 C14: minimum surfaced when below threshold (with caveat)
RAW_CANDIDATE_CAP  = 50

# ── BL1 — Signature route detection (BL0 v20260507, Section 10) ───────────────
BL1_CONCENTRATION_THRESHOLD = 0.40   # ≥40% of agent's multi-city corpus on top route
BL1_A_FREQ_MIN_THRESHOLD    = 5      # below this, fall to B (city-set)  — BL0 Q-D
BL1_AGENT_SIGNAL_THRESHOLD  = 10     # min multi-city tours to fire BL1  — BL0 Sec 9
BL1_RECENCY_CUTOFF_MONTHS   = 24     # corpus filter                      — BL0 Sec 4
BL1_MULTI_CITY_MIN          = 2      # multi-city = ≥2 cities             — BL0 Sec 3
BL1_REGION_MATCH_THRESHOLD  = 0.50   # ≥50% of route's cities in region   — BL0 Sec 10

# ── BL2-β — Recency decay weights (BL0 Sec 4 / shipped v0.5.6 12 May 2026) ───
# Applied in score_candidate() as multiplier. >24mo hard-drops via REFERENCE_FLOOR.
BL2_RECENCY_6MO  = 1.0   # ≤6 months  — full weight
BL2_RECENCY_12MO = 0.8   # ≤12 months
BL2_RECENCY_24MO = 0.5   # ≤24 months
BL2_RECENCY_OLD  = 0.0   # >24 months — hard-drop (filtered by REFERENCE_FLOOR = 0.0)

TODAY = date.today()


def parse_sequence(seq_text):
    if not seq_text or not seq_text.strip():
        return ()
    return tuple(p.strip() for p in seq_text.split('->') if p.strip())


def parse_iso_date(s):
    if not s:
        return None
    try:
        return datetime.strptime(s.strip(), '%Y-%m-%d').date()
    except (ValueError, AttributeError):
        return None


def effective_recency_date(start_date):
    if start_date is None:
        return None
    return TODAY if start_date > TODAY else start_date


def months_ago(d):
    if d is None:
        return 999
    return (TODAY - d).days / 30.44


REGION_TO_CITIES = {
    'rajasthan': {
        'Jaipur', 'Jodhpur', 'Udaipur (RJ)', 'Pushkar', 'Bundi', 'Bikaner',
        'Jaisalmer', 'Mandawa', 'Ranthambore', 'Ajmer', 'Narlai', 'Rohet',
        'Khimsar', 'Mount Abu', 'Chittorgarh', 'Deogarh',
    },
    'south_india': {
        'Chennai', 'Mamallapuram (Mahabalipuram)', 'Puducherry (Pondicherry)',
        'Madurai', 'Thanjavur (Tanjore)', 'Thekkady (Periyar/Kumily)',
        'Alappuzha (Alleppey)', 'Kochi (Cochin)', 'Munnar', 'Kumarakom',
        'Bengaluru', 'Mysuru (Mysore)', 'Wayanad', 'Kabini', 'Chidambaram',
        'Kumbakonam', 'Hampi (Hosapete)',
    },
    'north_india': {
        'New Delhi', 'Agra', 'Jaipur', 'Varanasi', 'Khajuraho',
        'Lucknow', 'Amritsar', 'Shimla', 'Chandigarh',
    },
    'wildlife': {
        'Bandhavgarh', 'Kanha', 'Pench', 'Panna', 'Satpura', 'Jabalpur',
        'Corbett', 'Ranthambore', 'Kaziranga',
    },
    'kerala': {
        'Kochi (Cochin)', 'Alappuzha (Alleppey)', 'Thekkady (Periyar/Kumily)',
        'Munnar', 'Kumarakom', 'Wayanad', 'Kovalam', 'Trivandrum',
    },
    # v0.5.1 C6: Engine-emitted regions previously missing from prototype.
    'central_india': {
        'Khajuraho', 'Bandhavgarh', 'Kanha', 'Pench (MP)', 'Pench', 'Satpura',
        'Orchha', 'Bhopal', 'Sanchi', 'Jabalpur', 'Gwalior',
        'Indore', 'Ujjain', 'Mandu', 'Pachmarhi',
    },
    'east_india': {
        'Kolkata', 'Darjeeling', 'Gangtok', 'Bhubaneswar', 'Puri',
        'Konark', 'Sundarbans', 'Pelling', 'Kalimpong', 'Lachen',
        'Lachung', 'Bagdogra',
    },
    'west_india': {
        'Mumbai', 'Pune', 'Aurangabad', 'Ajanta', 'Ellora',
        'Ahmedabad', 'Vadodara', 'Bhuj', 'Dwarka', 'Somnath',
        'Diu', 'Daman', 'Lonavala', 'Mahabaleshwar', 'Goa',
    },
    'northeast_india': {
        'Guwahati', 'Shillong', 'Kaziranga', 'Manas', 'Tawang',
        'Dirang', 'Bomdila', 'Cherrapunjee', 'Mawlynnong', 'Kohima',
        'Imphal', 'Aizawl',
    },
    'himalaya': {
        'Shimla', 'Manali', 'Dharamshala', 'McLeod Ganj', 'Dalhousie',
        'Leh', 'Nubra', 'Pangong', 'Srinagar', 'Gulmarg', 'Pahalgam',
        'Sonamarg', 'Rishikesh', 'Haridwar', 'Mussoorie', 'Nainital',
        'Ranikhet', 'Almora', 'Corbett',
    },
}


# ── Gateway cities ────────────────────────────────────────────────────────────
# Gateway cities are major transit/entry hubs that appear in routes regardless
# of the sub-region being visited. They are EXCLUDED from sub-region overlap
# calculation (neither counted nor penalised) — their presence in a sequence
# does not contribute to or detract from the sub-region match score.
#
# Principle: a city is a gateway when its primary role in a multi-region
# itinerary is as an entry/exit point rather than a destination in its own
# right for the sub-region. Delhi is always a gateway for Rajasthan; it is
# a destination when the sub-region IS north_india/golden_triangle.
#
# Gateway status is not absolute — a city can be both a gateway and a
# destination depending on context. The sub-region overlap logic handles
# this correctly: when sub_region='north_india', Delhi is NOT a gateway
# and counts toward overlap normally.
GATEWAY_CITIES = {
    'New Delhi',        # Gateway for all North India, Rajasthan, Himachal, UP, Uttarakhand
    'Mumbai',           # Gateway for West India, Goa, Maharashtra, South India
    'Chennai',          # Gateway for South India, Tamil Nadu
    'Kolkata',          # Gateway for East India, West Bengal, Sikkim, Northeast
    'Guwahati',         # Gateway for Northeast India
    'Bengaluru',        # Gateway for Karnataka, Kerala, South India
    'Kochi (Cochin)',   # Gateway for Kerala circuits
    'Hyderabad',        # Gateway for Andhra, Telangana
    'Ahmedabad',        # Gateway for Gujarat
    'Bagdogra',         # Gateway for Darjeeling, Sikkim
    'Jabalpur',         # Gateway for Central India wildlife parks
    'Bhopal',           # Gateway for Central India / Madhya Pradesh
    'Amritsar',         # Gateway for Punjab (also a destination — context-dependent)
}

# ── Sub-region city sets ───────────────────────────────────────────────────────
# Sub-regions are named states or circuits within a broader region. When the
# agent email explicitly mentions a sub-region (e.g. "Rajasthan", "Kerala",
# "Himachal"), the overlap calculation uses the sub-region city set rather than
# the full parent region — so Golden Triangle + Shimla scores low on Rajasthan
# overlap while Jaipur + Jodhpur + Jaisalmer scores high.
#
# Golden Triangle is NOT a sub-region — it is a canonical anchor circuit that
# competes for the primary slot on most North India requests. It earns its rank
# by how many sub-region cities it contains, not by a fixed position.
SUB_REGION_TO_CITIES = {
    'rajasthan': {
        'Jaipur', 'Jodhpur', 'Udaipur (RJ)', 'Jaisalmer', 'Bikaner',
        'Pushkar', 'Bundi', 'Mandawa', 'Ranthambore', 'Ajmer', 'Narlai',
        'Rohet', 'Khimsar', 'Mount Abu', 'Chittorgarh', 'Deogarh',
        'Shekhawati', 'Shekhala (Jodhpur - Jaisalmer Highway)', 'Jawai',
    },
    'kerala': {
        'Kochi (Cochin)', 'Munnar', 'Thekkady (Periyar/Kumily)',
        'Alappuzha (Alleppey)', 'Kumarakom', 'Kovalam', 'Varkala',
        'Wayanad', 'Trivandrum', 'Thrissur', 'Kannur',
    },
    'himachal': {
        'Shimla', 'Manali', 'Dharamshala', 'McLeod Ganj', 'Dalhousie',
        'Spiti Valley', 'Kasauli', 'Chail',
    },
    'uttarakhand': {
        'Rishikesh', 'Haridwar', 'Corbett', 'Mussoorie', 'Nainital',
        'Ranikhet', 'Almora', 'Auli', 'Jim Corbett',
    },
    'gujarat': {
        'Ahmedabad', 'Vadodara', 'Bhuj', 'Dwarka', 'Somnath',
        'Diu', 'Rann of Kutch', 'Sasan Gir', 'Palitana',
    },
    'karnataka': {
        'Mysuru (Mysore)', 'Hampi (Hosapete)', 'Coorg', 'Kabini',
        'Badami', 'Nagarhole', 'Chikmagalur',
    },
    'tamil_nadu': {
        'Madurai', 'Thanjavur (Tanjore)', 'Mamallapuram (Mahabalipuram)',
        'Ooty (Udhagamandalam)', 'Coonoor', 'Rameswaram', 'Kanyakumari',
        'Chidambaram', 'Kumbakonam', 'Puducherry (Pondicherry)',
    },
    'kashmir': {
        'Srinagar', 'Gulmarg', 'Pahalgam', 'Sonamarg',
    },
    'ladakh': {
        'Leh', 'Nubra Valley', 'Pangong Lake', 'Pangong', 'Nubra',
    },
    'punjab': {
        'Amritsar', 'Chandigarh', 'Anandpur Sahib',
    },
    'madhya_pradesh': {
        'Khajuraho', 'Orchha', 'Bandhavgarh', 'Kanha', 'Pench', 'Pench (MP)',
        'Bhopal', 'Sanchi', 'Gwalior', 'Indore', 'Ujjain', 'Mandu', 'Pachmarhi',
        'Satpura',
    },
    'odisha': {
        'Bhubaneswar', 'Puri', 'Konark',
    },
    'northeast': {
        'Guwahati', 'Kaziranga', 'Shillong', 'Cherrapunjee', 'Tawang',
        'Dirang', 'Manas', 'Bomdila',
    },
    'sikkim': {
        'Gangtok', 'Pelling', 'Lachen', 'Lachung', 'Ravangla',
    },
    'west_bengal': {
        'Kolkata', 'Darjeeling', 'Kalimpong',
    },
    'goa': {
        'Goa',
    },
    'andaman': {
        'Andaman Islands', 'Port Blair', 'Havelock Island',
    },
}


def expand_regions_to_cities(regions):
    cities = set()
    for r in regions:
        cities.update(REGION_TO_CITIES.get(r, set()))
    return cities


def get_overlap_cities(intent_cities, intent_regions, sub_region):
    """Return (relevant_cities, gateway_set) for overlap scoring.

    When sub_region is set (e.g. 'rajasthan'), uses the sub-region city set
    for overlap — so Golden Triangle + Shimla routes score low while pure
    Rajasthan routes score high. Gateway cities are excluded from the
    sub-region overlap set and passed back separately so callers can treat
    them as neutral (not counted, not penalised).

    When no sub_region: falls back to full region city set (existing behaviour).

    Returns:
        relevant_cities: set of cities to use for overlap calculation
        gateway_set:     set of gateway cities relevant to this request
                         (subset of GATEWAY_CITIES, not city-specific)
    """
    if sub_region and sub_region in SUB_REGION_TO_CITIES:
        sub_cities = SUB_REGION_TO_CITIES[sub_region]
        # Gateways are neutral — exclude from overlap set but track separately
        return sub_cities - GATEWAY_CITIES, GATEWAY_CITIES
    # No sub-region — use full region expansion (existing behaviour)
    relevant = set(intent_cities)
    if not relevant and intent_regions:
        relevant = expand_regions_to_cities(intent_regions)
    return relevant, set()


def passes_count_threshold(candidate, num_specified):
    """Adaptive: high-overlap matches need less volume."""
    overlap = candidate['_overlap_count']
    count   = candidate['booking_count']
    if num_specified < 3:
        return count >= 3
    overlap_ratio = overlap / num_specified
    if overlap_ratio >= 0.83:
        return count >= 1
    elif overlap_ratio >= 0.66:
        return count >= 2
    elif overlap_ratio >= 0.5:
        return count >= 3
    else:
        return count >= 5


def query_pass(db_path, where_clause, params, label, geography_cities=None):
    """Query master.db for city sequences matching where_clause.

    geography_cities: when set (global pass only), runs two sub-queries and
    merges them before returning:
      Sub-query A: top-100 sequences globally by booking_count (high-volume routes)
      Sub-query B: top-100 sequences containing ≥1 city from geography_cities
                   (geographically relevant routes — may not crack global top-100)
    This guarantees the global pass always contains both popular routes AND
    routes relevant to the requested geography — no separate region-scoped
    pass needed. Agent and market passes always pass geography_cities=None.
    """
    base_sql = """
        SELECT
            city_sequence,
            COUNT(*) AS booking_count,
            MAX(start_date) AS most_recent,
            agent_code,
            source_market
        FROM tours
        WHERE city_sequence IS NOT NULL
          AND city_sequence != ''
          AND start_date IS NOT NULL
          AND start_date != ''
          {where_clause}
        GROUP BY city_sequence
        ORDER BY booking_count DESC, most_recent DESC
        LIMIT {limit}
    """

    con = sqlite3.connect(db_path)

    # Sub-query A — top-100 by global volume (unchanged from original)
    sql_a = base_sql.format(where_clause=where_clause, limit=100)
    rows_a = con.execute(sql_a, params).fetchall()

    # Sub-query B — top-100 geographically relevant sequences (when requested)
    rows_b = []
    if geography_cities:
        like_clauses = " OR ".join(["city_sequence LIKE ?"] * len(geography_cities))
        geo_params   = tuple(f"%{c}%" for c in geography_cities)
        # Combine with any existing where_clause (agent/market filter)
        geo_where = f"{where_clause} AND ({like_clauses})" if where_clause.strip() else f"AND ({like_clauses})"
        sql_b = base_sql.format(where_clause=geo_where, limit=100)
        rows_b = con.execute(sql_b, params + geo_params).fetchall()

    con.close()

    # Merge A + B, deduplicate by city_sequence text (A wins on booking_count)
    seen = {}
    for r in rows_a + rows_b:
        key = r[0]  # city_sequence text
        if key not in seen or r[1] > seen[key][1]:
            seen[key] = r

    return [
        {
            'city_sequence': parse_sequence(r[0]),
            'sequence_text': r[0],
            'booking_count': r[1],
            'most_recent':   parse_iso_date(r[2]),
            'agent_code':    r[3],
            'source_market': r[4],
            'source_pass':   label,
        }
        for r in seen.values()
    ]


def relevance_filter(candidates, relevant_cities, num_specified_cities,
                     gateway_cities=None):
    """Filter candidates to those with meaningful overlap against relevant_cities.

    gateway_cities: when set (sub-region mode), these cities are excluded from
    the overlap count — they are present in sequences but treated as neutral.
    A sequence with Delhi + 3 Rajasthan cities scores overlap=3, not 4.
    """
    gateway_cities = gateway_cities or set()
    if num_specified_cities >= 3:
        min_required_overlap = max(2, int(num_specified_cities * OVERLAP_RATIO_FLOOR + 0.5))
    else:
        min_required_overlap = 1

    filtered = []
    for c in candidates:
        seq = c['city_sequence']
        if len(seq) < MIN_SEQ_LEN or len(seq) > MAX_SEQ_LEN:
            continue
        # Count only non-gateway cities in overlap
        overlap_count = sum(
            1 for city in seq
            if city in relevant_cities and city not in gateway_cities
        )
        if overlap_count < min_required_overlap:
            continue

        c['_overlap_count'] = overlap_count
        c['_overlap_ratio'] = overlap_count / len(relevant_cities) if relevant_cities else 0
        c['_recency_date']  = effective_recency_date(c['most_recent'])

        if not passes_count_threshold(c, num_specified_cities):
            continue
        filtered.append(c)

    return filtered, min_required_overlap


def _compute_agent_b_counts(db_path, account_code, region_cities):
    """C24 BL2-γ: Sequence-agnostic city-set counts for the agent's multi-city corpus.

    Queries the agent's tours (multi-city ≥2 cities, last 24 months), groups by
    frozenset of cities (B unit — sequence-agnostic), and returns a mapping
    {frozenset → count}.

    region_cities: set of canonical city names for the requested region/cities.
    Only city-sets with ≥1 city overlapping region_cities are included — keeps
    results focused on the relevant geography.

    Returns empty dict when account_code is absent or agent has no corpus.
    """
    if not account_code:
        return {}
    corpus = _agent_multi_city_corpus(db_path, account_code)
    b_counts = {}
    for seq, _seq_text, _sd in corpus:
        if len(seq) < BL1_MULTI_CITY_MIN:
            continue
        key = frozenset(seq)
        # Region relevance filter — drop city-sets with no overlap to region
        if region_cities and not key.intersection(region_cities):
            continue
        b_counts[key] = b_counts.get(key, 0) + 1
    return b_counts


def historical_query(intent, db_path=DB_PATH, verbose=False):
    cities       = list(intent.get('cities_detected', []) or [])
    regions      = intent.get('regions_detected', []) or []
    sub_region   = intent.get('sub_region')   # e.g. 'rajasthan', 'kerala' — set by engine parser
    # v0.5.2 C11: B27-AGENCY-LOOKUP fix — read engine-canonical keys first,
    # fall back to legacy keys so standalone prototype test cases still work.
    account_code = intent.get('agency_account_code') or intent.get('account_code')
    market       = intent.get('source_market')        or intent.get('market')

    # Sub-region overlap: when email explicitly names a state/circuit (e.g. 'Rajasthan'),
    # use the sub-region city set for overlap scoring rather than the full parent region.
    # Gateway cities (Delhi, Mumbai, etc.) are excluded from the overlap set and treated
    # as neutral — present in a sequence but neither counted nor penalised.
    # When no sub_region: falls back to full region expansion (existing behaviour).
    relevant_cities, gateway_cities = get_overlap_cities(cities, regions, sub_region)
    num_specified = len(cities)
    # Wildlife override: use anchor cities for both geography_boost AND relevance scoring
    if intent.get('_geography_override'):
        relevant_cities = set(intent['_geography_override'])
        gateway_cities  = set()

    if not relevant_cities:
        # For sub-region requests with no cities: relevant_cities comes from SUB_REGION dict.
        # If that's also empty, expand full region as final fallback.
        if regions:
            relevant_cities, gateway_cities = expand_regions_to_cities(regions), set()
        if not relevant_cities:
            if verbose:
                print("  ⚠ No cities or regions to filter by — returning empty.")
            return []

    if verbose:
        cities_preview = ', '.join(sorted(relevant_cities)[:6])
        more = f"... (+{len(relevant_cities)-6} more)" if len(relevant_cities) > 6 else ""
        print(f"  Relevant cities ({len(relevant_cities)}): {cities_preview}{more}")
        if sub_region:
            print(f"  Sub-region: {sub_region} — gateway cities neutral: "
                  f"{', '.join(sorted(gateway_cities)[:4])}...")
        print(f"  Specified cities: {num_specified}")

    # ── C1: All three passes always run ─────────────────────────
    agent_results = []
    if account_code:
        agent_results = query_pass(db_path, "AND agent_code = ?", (account_code,), 'agent')
        agent_results, _ = relevance_filter(agent_results, relevant_cities, num_specified, gateway_cities)
        if verbose:
            print(f"  Pass 1 (agent {account_code}): {len(agent_results)} candidates")

        # C25 BL2-γ: Two-stage B-fallback for sequence-diverse agents.
        #
        # Stage 1 (thin-A on surviving candidates): for agent candidates that DID
        # survive relevance_filter but have low literal-count (A_freq < threshold),
        # look up their B-count (sequence-agnostic city-set) and use that for
        # the frequency factor in score_candidate.
        #
        # Stage 2 (zero-survivors): for agents whose ALL literal sequences were
        # filtered out by passes_count_threshold (typically max per-sequence count ≤2
        # for sequence-diverse agents like Asia365), synthesize B-candidates directly
        # from the agent's city-set corpus and inject them into agent_results.
        # Synthesized candidates carry: city_sequence (canonical ordering from most
        # recent booking), booking_count=B_freq, agent_count=A_freq, source_pass='agent',
        # _b_driven=True, agent_b_count=B_freq.
        #
        # Both stages share the same _compute_agent_b_counts() call.
        agent_b_map = {}
        if account_code:
            agent_b_map = _compute_agent_b_counts(db_path, account_code, relevant_cities)

        # Stage 1 — attach B-count to thin-A survivors
        for c in agent_results:
            a_freq = c.get('agent_count', c['booking_count'])
            if a_freq < BL1_A_FREQ_MIN_THRESHOLD:
                city_set_key = frozenset(c['city_sequence'])
                b_freq = agent_b_map.get(city_set_key, 0)
                if b_freq > a_freq:
                    c['agent_b_count'] = b_freq
                    c['_b_driven']     = True
                    if verbose:
                        print(f"    BL2-γ B-fallback (Stage 1): "
                              f"{list(c['city_sequence'])} A={a_freq} → B={b_freq}")

        # Stage 2 — synthesize B-candidates when no agent survivors at all
        if not agent_results and agent_b_map:
            # Build canonical sequence for each city-set from _agent_multi_city_corpus
            # (most-recent literal sequence whose frozenset matches this key)
            b_canonical_text  = {}
            b_canonical_seq   = {}
            b_most_recent     = {}
            b_a_freq          = {}
            corpus = _agent_multi_city_corpus(db_path, account_code)
            for seq, seq_text, sd in corpus:
                key = frozenset(seq)
                if key not in agent_b_map:
                    continue
                prev = b_most_recent.get(key)
                if prev is None or sd > prev:
                    b_most_recent[key]     = sd
                    b_canonical_text[key]  = seq_text
                    b_canonical_seq[key]   = seq
                b_a_freq[key] = b_a_freq.get(key, 0) + 1  # literal count for this set

            # Filter to city-sets with ≥1 city overlapping relevant_cities
            for key, b_freq in sorted(agent_b_map.items(),
                                      key=lambda kv: kv[1], reverse=True):
                seq = b_canonical_seq.get(key)
                if not seq:
                    continue
                # Overlap check
                overlap_count = sum(1 for city in seq if city in relevant_cities)
                if overlap_count == 0:
                    continue
                # Build synthetic candidate
                sd = b_most_recent.get(key)
                synth = {
                    'city_sequence':  seq,
                    'sequence_text':  b_canonical_text.get(key, '->'.join(seq)),
                    'booking_count':  b_freq,       # B-count drives frequency
                    'agent_count':    b_a_freq.get(key, 1),
                    'most_recent':    sd,
                    'agent_code':     account_code,
                    'source_pass':    'agent',
                    'agent_b_count':  b_freq,
                    '_b_driven':      True,
                    '_overlap_count': overlap_count,
                    '_overlap_ratio': overlap_count / len(relevant_cities) if relevant_cities else 0,
                    '_recency_date':  effective_recency_date(sd),
                }
                agent_results.append(synth)
                if verbose:
                    print(f"    BL2-γ B-fallback (Stage 2 inject): "
                          f"{list(seq)} B={b_freq}")

    market_results = []
    if market:
        market_results = query_pass(db_path, "AND source_market = ?", (market,), 'market')
        market_results, min_overlap = relevance_filter(market_results, relevant_cities, num_specified, gateway_cities)
        if verbose:
            print(f"  Pass 2 (market {market}, min_overlap={min_overlap}): {len(market_results)} candidates")

    # ── Pass 3: Global — geography-aware ────────────────────────
    # Runs two sub-queries internally (query_pass with geography_cities):
    #   A: top-100 sequences globally by volume (high-volume routes)
    #   B: top-100 sequences containing ≥1 city from geography_boost
    #      (geographically relevant routes that may not crack global top-100)
    # When sub_region is active, use SUB_REGION_TO_CITIES[sub_region] as the
    # geography_boost — it is richer than REGION_TO_CITIES parent (e.g. rajasthan
    # has 19 cities including Ranthambore, vs north_india's 9 which omits it).
    # Without this, Sub-query B misses Rajasthan-specific sequences entirely.
    # When no sub_region, use full parent region expansion.
    # Relevance filter applies sub-region overlap + gateway exclusion as normal.
    if intent.get('_geography_override'):
        geography_boost = intent['_geography_override']
        print(f"  🔍 _geography_override ACTIVE: {geography_boost}")
    elif sub_region and sub_region in SUB_REGION_TO_CITIES:
        geography_boost = SUB_REGION_TO_CITIES[sub_region]
    elif regions:
        geography_boost = expand_regions_to_cities(regions)
    else:
        geography_boost = relevant_cities
    global_results = query_pass(db_path, "", (), 'global',
                                geography_cities=geography_boost or None)
    global_results, _ = relevance_filter(global_results, relevant_cities,
                                         num_specified, gateway_cities)
    if verbose:
        print(f"  Pass 3 (global, geography-aware): {len(global_results)} candidates")

    # ── C2: Merge with MAX booking_count across passes ──────────
    # Global has the truest "total bookings" count for any sequence.
    # Agent count comes from agent pass only.
    # Three tiers only: Agent / Market / Global — no Pass 4 or Pass 5.
    merged = {}

    def upsert(c, agent_count_field):
        seq = c['city_sequence']
        if seq in merged:
            if c['booking_count'] > merged[seq]['booking_count']:
                merged[seq]['booking_count'] = c['booking_count']
            if c.get('_recency_date') and (
                not merged[seq].get('_recency_date') or
                c['_recency_date'] > merged[seq]['_recency_date']
            ):
                merged[seq]['_recency_date'] = c['_recency_date']
                merged[seq]['most_recent']   = c['most_recent']
            if agent_count_field and merged[seq].get('agent_count', 0) == 0:
                merged[seq]['agent_count']  = c['booking_count']
                merged[seq]['agent_recent'] = c.get('_recency_date')
        else:
            base = {**c}
            base['agent_count']  = c['booking_count'] if agent_count_field else 0
            base['agent_recent'] = c.get('_recency_date') if agent_count_field else None
            merged[seq] = base

    for c in agent_results:
        upsert(c, agent_count_field=True)
    for c in market_results:
        upsert(c, agent_count_field=False)
    for c in global_results:
        upsert(c, agent_count_field=False)

    # ── C3: Sort and cap ─────────────────────────────────────────
    candidates = list(merged.values())
    candidates.sort(
        key=lambda c: (c.get('_overlap_count', 0), c['booking_count']),
        reverse=True
    )
    return candidates[:RAW_CANDIDATE_CAP]


def score_candidate(candidate, num_specified, requested_duration=None,
                    agent_total_bookings=0):
    if num_specified >= 1:
        overlap = candidate['_overlap_count'] / max(num_specified, 1)
    else:
        overlap = min(candidate['_overlap_count'] / 5.0, 1.0)
    overlap = min(overlap, 1.0)

    # v0.5 C4: log-scaled frequency, saturates at ~30 bookings.
    # C26 BL2-γ: when _b_driven flag set, use agent_b_count for frequency
    # instead of booking_count (B unit captures city-set volume, not literal-sequence).
    _b_driven = candidate.get('_b_driven', False)
    if _b_driven:
        freq_count = candidate.get('agent_b_count', candidate['booking_count'])
        freq_source = 'B (city-set)'
    else:
        freq_count = candidate['booking_count']
        freq_source = 'A (literal)'
    frequency = min(math.log(1 + freq_count) / math.log(31), 1.0)

    # BL2-β recency weights (v0.5.6 12 May 2026): 1.0/0.8/0.5/0.0
    # >24mo returns 0.0 — hard-drop via REFERENCE_FLOOR = 0.0 gate in assemble_options.
    m = months_ago(candidate.get('_recency_date'))
    if m <= 6:
        recency = BL2_RECENCY_6MO
    elif m <= 12:
        recency = BL2_RECENCY_12MO
    elif m <= 24:
        recency = BL2_RECENCY_24MO
    else:
        recency = BL2_RECENCY_OLD

    # v0.5 C5: ratio-aware affinity — tier on agent_count / booking_count ratio.
    agent_count = candidate.get('agent_count', 0)
    booking_count = candidate['booking_count']
    is_confident_agent = agent_total_bookings >= 3

    if not is_confident_agent or agent_count == 0:
        affinity = 1.0
    else:
        ratio = agent_count / max(booking_count, 1)
        if ratio >= 0.99:
            affinity = 3.0   # pure-agent signature
        elif ratio >= 0.5:
            affinity = 2.0   # mostly agent's pattern
        else:
            affinity = 1.3   # one of many agents

    # v0.5.1 C8: Engine emits (lo, hi) tuple for date-range / "8-10 nights"
    # requests. Normalise to scalar midpoint internally so callers don't have
    # to pre-process. None passes through unchanged.
    if isinstance(requested_duration, tuple):
        if len(requested_duration) == 2 and all(isinstance(x, int) for x in requested_duration):
            requested_duration = (requested_duration[0] + requested_duration[1]) // 2
        else:
            requested_duration = None  # malformed — treat as unknown

    if requested_duration is None:
        duration_flex = 1.0
    else:
        approx_duration = len(candidate['city_sequence']) + 2
        diff = abs(approx_duration - requested_duration)
        if diff <= 1:
            duration_flex = 1.0
        elif diff <= 3:
            duration_flex = 0.7
        else:
            return 0.0, None

    score = overlap * frequency * recency * affinity * duration_flex
    breakdown = {
        'overlap':       round(overlap, 2),
        'frequency':     round(frequency, 2),
        'freq_source':   freq_source,
        'recency':       round(recency, 2),
        'affinity':      round(affinity, 2),
        'duration_flex': round(duration_flex, 2),
        'score':         round(score, 3),
    }
    return score, breakdown


def build_label(candidate, agent_name=None):
    count    = candidate['booking_count']
    agent_ct = candidate.get('agent_count', 0)
    recent   = candidate.get('_recency_date')

    if recent:
        m = months_ago(recent)
        if m < 1:
            recent_str = 'this month'
        elif m < 24:
            recent_str = f'{int(m)} mo ago'
        else:
            recent_str = f'{int(m/12)} yr ago'
    else:
        recent_str = '—'

    if agent_ct >= 1 and agent_name:
        # C27 BL2-γ: distinguish A (literal) vs B (city-set) attribution
        if candidate.get('_b_driven'):
            b_ct = candidate.get('agent_b_count', agent_ct)
            return f"[{agent_name}'s city-set match · {b_ct} bookings · last {recent_str}]"
        return f"[{agent_name}'s pattern · {agent_ct} of {count} bookings · last {recent_str}]"
    elif candidate['source_pass'] == 'market':
        market = candidate.get('source_market', '?')
        return f"[Popular pattern · {count} bookings {market} market · last {recent_str}]"
    else:
        return f"[Popular pattern · {count} bookings all markets · last {recent_str}]"


SPARSE_TEMPLATE_REGIONS = {
    'central_india', 'east_india', 'northeast_india', 'himalaya',
    'west_india',  # less sparse than the others but still custom-strung
    'wildlife',    # camp-circuit tours don't repeat as exact sequences
}


# ─── BL1: signature route detection (BL0 v20260507, Section 10) ──────────────

def _bl1_recency_in_window(start_date, today=None):
    """BL0 Sec 4: tour falls within last BL1_RECENCY_CUTOFF_MONTHS."""
    if start_date is None:
        return False
    today = today or TODAY
    return ((today - start_date).days / 30.44) <= BL1_RECENCY_CUTOFF_MONTHS


def _agent_multi_city_corpus(db_path, account_code):
    """Returns agent's tours filtered to multi-city (≥BL1_MULTI_CITY_MIN
    cities) AND within the last BL1_RECENCY_CUTOFF_MONTHS.

    BL0 Sec 3 — multi-city filter for pattern computation. Single-city tours
    are operationally distinct (transit / short-stay) and would distort the
    concentration denominator if included.

    Returns list of (sequence_tuple, sequence_text, start_date) tuples.
    """
    if not account_code:
        return []
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT city_sequence, start_date FROM tours "
            "WHERE agent_code = ? "
            "  AND city_sequence IS NOT NULL "
            "  AND city_sequence != '' "
            "  AND start_date IS NOT NULL "
            "  AND start_date != ''",
            (account_code,)
        ).fetchall()
    finally:
        con.close()

    result = []
    for seq_text, sd_str in rows:
        seq = parse_sequence(seq_text)
        if len(seq) < BL1_MULTI_CITY_MIN:
            continue
        sd = parse_iso_date(sd_str)
        if sd is None:
            continue
        # effective_recency_date handles future-dated bookings (treats them
        # as TODAY) — keeps forward bookings in the window correctly.
        eff = effective_recency_date(sd)
        if not _bl1_recency_in_window(eff):
            continue
        result.append((seq, seq_text, sd))
    return result


def _route_matches_region(sequence, request_region_set):
    """BL0 Sec 10 — signature region must match request region. Returns True
    when at least BL1_REGION_MATCH_THRESHOLD fraction of the sequence's
    cities are in the request_region_set. Empty region_set short-circuits
    True (no constraint to enforce — caller decides whether to skip BL1)."""
    if not request_region_set:
        return True
    if not sequence:
        return False
    matching = sum(1 for c in sequence if c in request_region_set)
    return (matching / len(sequence)) >= BL1_REGION_MATCH_THRESHOLD


def _bl1_should_fire(intent):
    """BL0 Sec 1 — BL1 does NOT fire for Type 3 (explicit route) requests.

    Type 3 detection signals (per BL0 Table 'Type detection'):
      - intent.explicit_itinerary populated
      - intent._input_mode in ('TOURLANE', 'CSV', 'PDF')
    """
    if intent.get('explicit_itinerary'):
        return False
    if intent.get('_input_mode') in ('TOURLANE', 'CSV', 'PDF'):
        return False
    return True


def compute_signature_route(db_path, account_code, request_region_set):
    """BL1 entry point.

    Fires when:
      1. Agent has ≥BL1_AGENT_SIGNAL_THRESHOLD multi-city, last-24mo tours
      2. Top route's concentration ≥ BL1_CONCENTRATION_THRESHOLD
      3. Top route's cities majority-overlap request_region_set

    A primary, B fallback (BL0 Q-D, Mechanism 1):
      - If top A_freq ≥ BL1_A_FREQ_MIN_THRESHOLD: A drives
      - Else: fall to top B (sequence-agnostic city-set count)

    Returns dict on fire, None otherwise.

    Returned dict shape:
      {
        'sequence':              tuple,   # parsed city sequence
        'sequence_text':         str,     # raw '->' string from DB
        'a_freq':                int,     # literal-sequence count
        'b_freq':                int,     # city-set count
        'concentration':         float,   # 0.0–1.0 (a_freq/total or b_freq/total)
        'agent_total_multi_city': int,    # denominator (filtered corpus size)
        'most_recent':           date,    # latest start_date for this route
        'driven_by':             'A' or 'B',
      }
    """
    corpus = _agent_multi_city_corpus(db_path, account_code)
    if len(corpus) < BL1_AGENT_SIGNAL_THRESHOLD:
        return None

    total = len(corpus)

    # Literal-sequence (A): count + most-recent date per sequence_text
    a_counts = {}
    a_recent = {}
    for seq, seq_text, sd in corpus:
        a_counts[seq_text] = a_counts.get(seq_text, 0) + 1
        prev = a_recent.get(seq_text)
        if prev is None or sd > prev:
            a_recent[seq_text] = sd

    # Sequence-agnostic city-set (B): count + most-recent date + canonical
    # sequence_text (the most-recent literal sequence whose cities form this set)
    b_counts = {}
    b_recent = {}
    b_canonical_text = {}
    for seq, seq_text, sd in corpus:
        key = frozenset(seq)
        b_counts[key] = b_counts.get(key, 0) + 1
        prev = b_recent.get(key)
        if prev is None or sd > prev:
            b_recent[key]         = sd
            b_canonical_text[key] = seq_text

    # ── Decision: A primary, B fallback ───────────────────────────
    top_a_text  = max(a_counts, key=a_counts.get)
    top_a_count = a_counts[top_a_text]

    if top_a_count >= BL1_A_FREQ_MIN_THRESHOLD:
        # A drives
        concentration = top_a_count / total
        if concentration < BL1_CONCENTRATION_THRESHOLD:
            return None
        seq = parse_sequence(top_a_text)
        if not _route_matches_region(seq, request_region_set):
            return None
        return {
            'sequence':               seq,
            'sequence_text':          top_a_text,
            'a_freq':                 top_a_count,
            'b_freq':                 b_counts.get(frozenset(seq), top_a_count),
            'concentration':          concentration,
            'agent_total_multi_city': total,
            'most_recent':            a_recent[top_a_text],
            'driven_by':              'A',
        }

    # A below threshold — fall to B
    top_b_set   = max(b_counts, key=b_counts.get)
    top_b_count = b_counts[top_b_set]
    concentration_b = top_b_count / total
    if concentration_b < BL1_CONCENTRATION_THRESHOLD:
        return None

    seq_text = b_canonical_text[top_b_set]
    seq = parse_sequence(seq_text)
    if not _route_matches_region(seq, request_region_set):
        return None

    return {
        'sequence':               seq,
        'sequence_text':          seq_text,
        'a_freq':                 a_counts.get(seq_text, 0),
        'b_freq':                 top_b_count,
        'concentration':          concentration_b,
        'agent_total_multi_city': total,
        'most_recent':            b_recent[top_b_set],
        'driven_by':              'B',
    }


def _bl1_label(signature, agent_name=None):
    """Build the BL0-spec label for a signature route.
      [Your literal pattern · N bookings · X% concentration · last <recency>]   (A drives)
      [Your city-set match · N bookings · X% concentration · last <recency>]    (B drives)
    """
    if signature['driven_by'] == 'A':
        kind = "literal pattern"
        n    = signature['a_freq']
    else:
        kind = "city-set match"
        n    = signature['b_freq']

    recent = signature.get('most_recent')
    if recent:
        m = months_ago(recent)
        if m < 1:
            recent_str = 'this month'
        elif m < 24:
            recent_str = f'{int(m)} mo ago'
        else:
            recent_str = f'{int(m/12)} yr ago'
        recent_part = f" · last {recent_str}"
    else:
        recent_part = ""

    pct = round(signature['concentration'] * 100)
    return f"[Your {kind} · {n} bookings · {pct}% concentration{recent_part}]"


def _compute_diagnostic(intent, scored_count, filtered_count):
    """Build diagnostic info — counts + heuristic reason for caveat / empty cases.

    Reason heuristics (most specific first):
      - filtered_total == 0 + sparse-template region   → v2 explanation
      - filtered_total == 0                            → no overlap
      - scored == 0 + duration was specified           → duration mismatch
      - scored < 3                                     → low overall match quality
    """
    cities  = intent.get('cities_detected', []) or []
    regions = intent.get('regions_detected', []) or []
    duration = intent.get('duration_nights')

    if filtered_count == 0:
        if not cities and any(r in SPARSE_TEMPLATE_REGIONS for r in regions):
            reason = ("sparse-template region — tours here are typically "
                      "custom-strung itineraries. Exact-sequence matching "
                      "can't aggregate them. (B27-v2 city-set mining will "
                      "close this gap.)")
        else:
            reason = "no historical sequences match the requested cities"
    elif scored_count == 0:
        if duration is not None:
            d_disp = (f"{duration[0]}-{duration[1]}"
                      if isinstance(duration, tuple) else f"{duration}")
            reason = (f"requested duration ({d_disp}n) doesn't fit "
                      f"historical sequences (typical 6–9n)")
        else:
            reason = ("all candidates filtered out — likely overlap or "
                      "volume threshold")
    else:
        reason = ("low overall match quality — partial overlap, low "
                  "recency, or low historical volume")

    return {
        'filtered_total':     filtered_count,
        'scored_above_floor': scored_count,
        'reason':             reason,
    }


def _fetch_nightly_split_for_options(db_path, options):
    """v0.5.4 C16: For each option, look up the most-recent matching booking
    by city_sequence and attach its per-city nightly split.

    Sets `_nightly_split` (list[int] of len == len(city_sequence)) and
    `_estimated_duration` (sum of nightly_split) on each option in place.

    Source path:
      1. tours.file_code  ← most recent row matching city_sequence (start_date DESC)
      2. services.* WHERE file_code = ? AND record_type = 'Accommodation'
      3. Aggregate nights per city_name from check_out − check_in (days).
      4. Project onto sequence positions; missing cities default to 1n.

    Fallback: if no matching booking or services data is unparseable, use
    [1] * len(sequence) + 2 spare distributed across mid-sequence positions.
    """
    if not options:
        return

    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        for opt in options:
            seq_cities = opt['city_sequence']
            seq_text   = opt.get('sequence_text')

            split = None
            if seq_text and seq_cities:
                cur.execute(
                    "SELECT file_code FROM tours "
                    "WHERE city_sequence = ? "
                    "ORDER BY start_date DESC LIMIT 1",
                    (seq_text,)
                )
                row = cur.fetchone()
                if row:
                    file_code = row[0]
                    cur.execute(
                        "SELECT DISTINCT city_name, check_in, check_out FROM services "
                        "WHERE file_code = ? AND record_type = 'Accommodation' "
                        "AND check_in != '' AND check_out != ''",
                        (file_code,)
                    )
                    nights_by_city = {}
                    for city, ci, co in cur.fetchall():
                        try:
                            ci_d = datetime.strptime(ci, '%Y-%m-%d').date()
                            co_d = datetime.strptime(co, '%Y-%m-%d').date()
                            n = (co_d - ci_d).days
                            if n > 0:
                                nights_by_city[city] = nights_by_city.get(city, 0) + n
                        except (ValueError, TypeError):
                            continue
                    if nights_by_city:
                        # Project onto sequence positions; default missing cities to 1n
                        # (rare — should match since city_sequence is derived from these
                        # same accommodation services during master.db build)
                        split = [nights_by_city.get(city, 1) for city in seq_cities]

            # Fallback: even distribution
            if split is None:
                n_cities = len(seq_cities)
                split = [1] * n_cities
                if n_cities >= 4:
                    # 2 spare nights given to mid-sequence cities (typical pacing)
                    mid = n_cities // 2
                    split[mid - 1] += 1
                    split[mid] += 1

            assert len(split) == len(seq_cities), \
                f"v0.5.4 nightly_split length mismatch: {len(split)} vs {len(seq_cities)}"

            opt['_nightly_split']      = split
            opt['_estimated_duration'] = sum(split)
    finally:
        con.close()


def assemble_options(candidates, intent, agent_name=None, db_path=None):
    """Return result envelope: {options, caveat, diagnostic}.

    v0.5.3 C13: envelope replaces bare list. v0.5.3 C14: single ranked list,
    no promote/ref split, top 10 cap with min-3 below-threshold fallback.
    v0.5.4 C16/C17: each option carries _nightly_split + _estimated_duration
    (most-recent matching booking; falls back to even distribution).

    Display rule:
      ≥ 1 option scores ≥ PROMOTE_THRESHOLD  →  top 10, no caveat
      ≥ 1 option scores > 0                  →  top 3 + caveat banner
      else                                    →  empty options + diagnostic
    """
    num_specified  = len(intent.get('cities_detected', []) or [])
    duration       = intent.get('duration_nights')
    agent_bookings = intent.get('_agent_total_bookings', 0)
    # v0.5.2 C12: auto-source agent_name from intent (recommend() integration path)
    if agent_name is None:
        agent_name = intent.get('agency_name')

    # Score every candidate; keep anything with score > 0 (v0.5.3 C14 — no floor)
    scored = []
    for c in candidates:
        score, breakdown = score_candidate(c, num_specified, duration, agent_bookings)
        if score <= REFERENCE_FLOOR:   # 0.0 — drops only score_candidate's hard-zero returns
            continue
        c['_score']     = score
        c['_breakdown'] = breakdown
        c['_label']     = build_label(c, agent_name)
        scored.append(c)

    scored.sort(key=lambda c: c['_score'], reverse=True)

    # v0.5.1 C9: Prefix-dedup
    def _same_month(d1, d2):
        if d1 is None or d2 is None:
            return d1 == d2
        return d1.year == d2.year and d1.month == d2.month

    def _similar_count(a, b):
        return abs(a - b) <= max(a, b) * 0.5

    deduped = []
    for c in scored:
        seq_a = c['city_sequence']
        is_prefix_of_kept = False
        for k in deduped:
            seq_b = k['city_sequence']
            if (len(seq_b) > len(seq_a)
                and tuple(seq_b[:len(seq_a)]) == tuple(seq_a)
                and _similar_count(c['booking_count'], k['booking_count'])
                and _same_month(c.get('most_recent'), k.get('most_recent'))):
                is_prefix_of_kept = True
                break
        if is_prefix_of_kept:
            continue
        deduped = [k for k in deduped if not (
            len(c['city_sequence']) > len(k['city_sequence'])
            and tuple(c['city_sequence'][:len(k['city_sequence'])]) == tuple(k['city_sequence'])
            and _similar_count(c['booking_count'], k['booking_count'])
            and _same_month(c.get('most_recent'), k.get('most_recent'))
        )]
        deduped.append(c)

    # v0.5.4 C16: resolve db_path lazily (defaults to module DB_PATH)
    _db_path = db_path or DB_PATH

    # ── v0.5.5 BL1: signature route detection (BL0 v20260507, Section 10) ───
    # Run AFTER scoring + dedup, BEFORE envelope assembly. If signature fires
    # AND a candidate matches its sequence_text, relabel that candidate and
    # force it to position 0. If the signature route isn't in the deduped
    # list (rare — likely deduped by a longer prefix-related sequence), the
    # signature is computed but no override happens. v0.5.5 does not synthesize
    # missing candidates; that's deferred to BL2.
    signature = None
    if _bl1_should_fire(intent):
        bl1_account_code = (intent.get('agency_account_code')
                            or intent.get('account_code'))
        bl1_regions      = intent.get('regions_detected') or []
        if bl1_account_code and bl1_regions:
            bl1_region_set = expand_regions_to_cities(bl1_regions)
            signature = compute_signature_route(
                _db_path, bl1_account_code, bl1_region_set
            )

    if signature:
        sig_seq_text = signature['sequence_text']
        match_idx = None
        for i, c in enumerate(deduped):
            if c.get('sequence_text') == sig_seq_text:
                match_idx = i
                break
        if match_idx is not None:
            sig_candidate = deduped.pop(match_idx)
            sig_candidate['_label']               = _bl1_label(signature, agent_name)
            sig_candidate['_bl1_fired']           = True
            sig_candidate['_bl1_concentration']   = signature['concentration']
            sig_candidate['_bl1_driven_by']       = signature['driven_by']
            sig_candidate['_bl1_corpus_total']    = signature['agent_total_multi_city']
            deduped.insert(0, sig_candidate)
        # else: signature exists but the sequence is not in deduped (likely
        # deduped by a longer related sequence, or filtered by relevance/count).
        # Skip silently — existing label on the related candidate already
        # conveys agent-affinity via the v0.5 ratio-based affinity boost.

    # Build the envelope based on display rule
    diagnostic = _compute_diagnostic(
        intent,
        scored_count=len(deduped),
        filtered_count=len(candidates),
    )

    if not deduped:
        # Empty/diagnostic-only state — no options to enrich
        return {
            'options': [],
            'caveat':  None,
            'diagnostic': diagnostic,
        }

    top_score = deduped[0]['_score']

    if top_score >= PROMOTE_THRESHOLD:
        # Normal state — show top 10, no caveat
        final_options = deduped[:TOP_N_OPTIONS]
        _fetch_nightly_split_for_options(_db_path, final_options)
        return {
            'options': final_options,
            'caveat':  None,
            'diagnostic': diagnostic,
        }

    # Caveat state — nothing reached threshold; surface min-3 with banner
    caveat = (
        "⚠ No routes scored above the recommendation threshold.\n"
        f"   Showing the {min(MIN_OPTIONS_DISPLAY, len(deduped))} best partial matches below threshold.\n"
        f"   Likely cause: {diagnostic['reason']}."
    )
    final_options = deduped[:MIN_OPTIONS_DISPLAY]
    _fetch_nightly_split_for_options(_db_path, final_options)
    return {
        'options': final_options,
        'caveat':  caveat,
        'diagnostic': diagnostic,
    }


def get_agent_total_bookings(db_path, account_code):
    if not account_code:
        return 0
    con = sqlite3.connect(db_path)
    cnt = con.execute(
        "SELECT COUNT(*) FROM tours WHERE agent_code = ?", (account_code,)
    ).fetchone()[0]
    con.close()
    return cnt


TEST_CASES = [
    {'name': 'TC1: Audley GBR South India',
     'agent_name': 'Audley Travel',
     'intent': {'cities_detected': ['Chennai', 'Mamallapuram (Mahabalipuram)',
                                    'Madurai', 'Thekkady (Periyar/Kumily)', 'Kochi (Cochin)'],
                'regions_detected': ['south_india'], 'duration_nights': 12,
                'account_code': 'ACC0131', 'market': 'GBR'}},
    {'name': 'TC2: Audley GBR Rajasthan',
     'agent_name': 'Audley Travel',
     'intent': {'cities_detected': ['New Delhi', 'Jodhpur', 'Udaipur (RJ)', 'Jaipur', 'Agra'],
                'regions_detected': ['rajasthan'], 'duration_nights': 10,
                'account_code': 'ACC0131', 'market': 'GBR'}},
    {'name': 'TC3: Region only, no cities',
     'agent_name': None,
     'intent': {'cities_detected': [], 'regions_detected': ['rajasthan'],
                'duration_nights': 9, 'account_code': None, 'market': 'FRA'}},
    {'name': 'TC4: Hobo — niche Rajasthan with Pushkar+Bundi',
     'agent_name': None,
     'intent': {'cities_detected': ['New Delhi', 'Jodhpur', 'Pushkar', 'Bundi',
                                    'Udaipur (RJ)', 'Jaipur'],
                'regions_detected': ['rajasthan'], 'duration_nights': 9,
                'account_code': None, 'market': 'BEL'}},
    {'name': 'TC5: New agent, Golden Triangle',
     'agent_name': None,
     'intent': {'cities_detected': ['New Delhi', 'Agra', 'Jaipur'],
                'regions_detected': ['north_india'], 'duration_nights': 7,
                'account_code': None, 'market': 'AUS'}},
]


def print_options(result):
    """Render the result envelope to terminal. Three layouts:

    (a) Normal      — options present, top score ≥ 0.50, no caveat
    (b) Caveat      — options present (1-3), top score < 0.50, banner above
    (c) Empty       — no options, diagnostic-only message

    v0.5.3 C15: accepts envelope dict from assemble_options. For backward
    compatibility, also accepts a bare list (legacy callers).
    """
    # Backward compat — wrap legacy bare list into a minimal envelope
    if isinstance(result, list):
        result = {'options': result, 'caveat': None, 'diagnostic': None}

    options    = result.get('options') or []
    caveat     = result.get('caveat')
    diagnostic = result.get('diagnostic') or {}

    # Layout (c) — empty state
    if not options:
        print()
        print("  No historical patterns match this request shape.")
        if diagnostic.get('reason'):
            print(f"    Reason: {diagnostic['reason']}")
        return

    # Layout (b) — caveat banner above table
    if caveat:
        print()
        for line in caveat.splitlines():
            print(f"  {line}")

    # Layouts (a) and (b) share the same table format
    print(f"\n  {'#':>2}  {'Score':>5}  {'Pass':>6}  Sequence + Label")
    print("  " + "─" * 110)
    for i, c in enumerate(options, 1):
        future_marker = '↑' if c.get('most_recent') and c['most_recent'] > TODAY else ''

        # v0.5.4 C18: build "City Nn" items from _nightly_split (length-aligned to sequence)
        seq_cities = list(c['city_sequence'])
        nightly    = c.get('_nightly_split') or [None] * len(seq_cities)
        items = [
            f"{city} {n}n" if isinstance(n, int) else city
            for city, n in zip(seq_cities, nightly)
        ]

        WRAP_AT = 5  # v0.5.4: tighter wrap because each item is wider with "Nn" suffix
        first_line = ' → '.join(items[:WRAP_AT])
        rest_items = items[WRAP_AT:]

        # P2-08 (v20260522b): cap display at 100% — BL2-γ city-set match can
        # push _score above 1.0 for strong agent matches; show 100% not 104%.
        score_pct  = min(round(c['_score'] * 100), 100)
        score_disp = f"{score_pct}%"

        print(f"  {i:>2}  {score_disp:>5}  {c['source_pass']:>6}  "
              f"{first_line}{'' if rest_items else future_marker}")

        while rest_items:
            chunk = rest_items[:WRAP_AT]
            rest_items = rest_items[WRAP_AT:]
            tail_marker = future_marker if not rest_items else ''
            print(f"      {' ' * 17}  → {' → '.join(chunk)}{tail_marker}")

        print(f"      {c['_label']}")


def main():
    print("=" * 70)
    print(f"  B27 HISTORICAL QUERY  v0.5.4b  (today = {TODAY})")
    print("=" * 70)
    print(f"  Threshold: {round(PROMOTE_THRESHOLD * 100)}%  ·  Cap: top {TOP_N_OPTIONS}  ·  "
          f"Min display below threshold: {MIN_OPTIONS_DISPLAY}")
    print("  v0.5.4: nightly_split sourced from most-recent matching booking  ·  "
          "scores as percentage")

    for tc in TEST_CASES:
        print(f"\n{'═' * 70}\n  {tc['name']}\n{'═' * 70}")
        print(f"  Cities:   {tc['intent']['cities_detected']}")
        print(f"  Regions:  {tc['intent']['regions_detected']}")
        print(f"  Agent:    {tc['intent']['account_code']} ({tc['agent_name']})")
        print(f"  Market:   {tc['intent']['market']}")
        print(f"  Duration: {tc['intent']['duration_nights']}n\n")

        agent_total = get_agent_total_bookings(DB_PATH, tc['intent']['account_code'])
        tc['intent']['_agent_total_bookings'] = agent_total
        if agent_total:
            print(f"  Agent has {agent_total} total bookings in master.db")

        candidates = historical_query(tc['intent'], verbose=True)
        print(f"\n  → {len(candidates)} raw candidates after merge + filter")

        result = assemble_options(candidates, tc['intent'], tc['agent_name'])
        n_options = len(result['options'])
        above_thresh = sum(1 for o in result['options']
                           if o['_score'] >= PROMOTE_THRESHOLD)
        state = (
            'NORMAL' if result['caveat'] is None and n_options > 0
            else 'CAVEAT' if result['caveat'] else 'EMPTY'
        )
        print(f"  → {n_options} options  ·  {above_thresh} ≥ threshold  ·  state: {state}")
        print_options(result)


if __name__ == '__main__':
    main()


# ── Wildlife Historical Query ─────────────────────────────────────────────────

WILDLIFE_ZONES = [
    {
        'name':    'Ranthambore',
        'cities':  ['Ranthambore'],
        'regions': ['north_india'],
    },
    {
        'name':    'Central India',
        'cities':  ['Bandhavgarh', 'Kanha', 'Pench'],
        'regions': ['central_india'],
    },
    {
        'name':    'Jim Corbett',
        'cities':  ['Corbett'],
        'regions': ['north_india'],
    },
    {
        'name':    'South India',
        'cities':  ['Kabini', 'Wayanad'],
        'regions': ['south_india'],
    },
    {
        'name':    'Northeast',
        'cities':  ['Kaziranga'],
        'regions': ['northeast_india'],
    },
]


def wildlife_historical_query(intent, db_path='master_v2.db'):
    """
    Runs one focused historical_query per wildlife zone.
    Three-tier (agent → market → global) per zone.
    Zones with no results above threshold are suppressed.

    Returns a list of zone dicts:
    [
        {
            'zone':    'Ranthambore',
            'options': [opt_agent, opt_market, opt_global],  # None if no data
        },
        ...
    ]
    Each opt is a standard option dict from assemble_options, or None.
    """
    results = []

    for zone in WILDLIFE_ZONES:
        zone_intent = dict(intent)
        zone_intent['cities_detected']    = zone['cities']
        zone_intent['regions_detected']   = zone['regions']
        zone_intent['sub_region']         = None
        zone_intent['_geography_override'] = None  # disable wildlife override for zone queries

        candidates = historical_query(zone_intent, db_path=db_path)
        if not candidates:
            continue

        # Run assemble_options — get best per tier
        envelope = assemble_options(candidates, zone_intent)
        options  = envelope.get('options', [])

        if not options:
            continue

        # Pick best per pass (agent → market → global), max 1 each
        best = {'agent': None, 'market': None, 'global': None}
        for opt in options:
            pass_label = opt.get('source_pass', 'global')
            if pass_label in best and best[pass_label] is None:
                best[pass_label] = opt

        # Suppress zone entirely if nothing above threshold
        above = [o for o in options if o.get('_score', 0) >= WILDLIFE_PROMOTE_THRESHOLD]
        if not above:
            continue

        # Fetch nightly splits explicitly — assemble_options only does this for
        # options scoring >= PROMOTE_THRESHOLD (0.50). Wildlife options sit between
        # WILDLIFE_PROMOTE_THRESHOLD (0.10) and 0.49 so they never get splits
        # from assemble_options. Call directly on the best-per-tier set.
        zone_options = [o for o in [best['agent'], best['market'], best['global']] if o is not None]
        _fetch_nightly_split_for_options(db_path, zone_options)

        results.append({
            'zone':    zone['name'],
            'options': [best['agent'], best['market'], best['global']],
        })

    return results


def print_wildlife_options(zone_results):
    """
    Renders wildlife historical routes in the same visual style
    as print_options — zone headers + consistent route format.
    """
    if not zone_results:
        print("  ⬜ No historical wildlife routes above threshold.")
        return

    counter = 1
    for zone_data in zone_results:
        zone_name = zone_data['zone']
        options   = zone_data['options']

        print(f"\n  ── {zone_name} ──")
        print(f"  {'─' * (len(zone_name) + 6)}")

        for opt in options:
            if opt is None:
                continue
            score      = opt.get('_score', 0)
            pass_label = opt.get('source_pass', 'global')
            label      = opt.get('_label', '')

            # Build sequence string — mirrors print_options: city_sequence + _nightly_split
            seq_cities = list(opt.get('city_sequence') or [])
            nightly    = opt.get('_nightly_split') or [None] * len(seq_cities)
            if seq_cities:
                items = [
                    f"{city} {n}n" if isinstance(n, int) else city
                    for city, n in zip(seq_cities, nightly)
                ]
                seq_str = ' → '.join(items)
            else:
                # fallback: raw sequence_text (should rarely reach here after Fix 1)
                seq_str = opt.get('sequence_text', '')

            # Wrap long sequences
            WRAP = 90
            if len(seq_str) > WRAP:
                words = seq_str.split(' → ')
                lines = []
                current = []
                for w in words:
                    current.append(w)
                    if len(' → '.join(current)) > WRAP:
                        last = current.pop()
                        lines.append(' → '.join(current))
                        current = [last]
                if current:
                    lines.append(' → '.join(current))
                seq_str = ('\n' + ' ' * 16).join(lines)

            print(f"  {counter:2}  {min(round(score*100), 100):3}%  {pass_label:>6}  {seq_str}")
            print(f"      {label}")
            counter += 1
