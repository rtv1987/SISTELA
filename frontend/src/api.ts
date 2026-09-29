const prefix = import.meta.env.DEV ? '/api' : '';
export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(prefix + path, { ...options, headers: { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers } });
  if (!response.ok) {
    let detail = `Užklausa nepavyko (${response.status})`;
    try { const value = await response.json(); detail = typeof value.detail === 'string' ? value.detail : 'Neteisinga reikšmė. Patikrinkite privalomus laukus ir skaičius.'; } catch { /* preserve status */ }
    throw new Error(detail);
  }
  return response.json();
}
export const post = <T,>(path: string, body: unknown = {}) => api<T>(path, { method: 'POST', body: JSON.stringify(body) });
export const apiUrl = (path: string) => prefix + path;
