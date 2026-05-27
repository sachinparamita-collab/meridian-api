const BASE = 'https://meridian-api-production-8184.up.railway.app';
export async function recommend(emailText, apiKey) {
  const res = await fetch(`${BASE}/v1/recommend`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-API-Key': apiKey },
    body: JSON.stringify({ email_text: emailText }),
  });
  if (!res.ok) { const err = await res.json().catch(() => ({})); throw new Error(err.detail || `API error ${res.status}`); }
  return res.json();
}
export async function healthCheck(apiKey) {
  const res = await fetch(`${BASE}/v1/health`, { headers: { 'X-API-Key': apiKey } });
  return res.ok;
}
