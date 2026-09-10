let token = '';
export async function api<T>(path: string, body?: object): Promise<T> {
  const response = await fetch(`/api${path}`, { method: body === undefined ? 'GET' : 'POST', headers: body === undefined ? {} : { 'Content-Type': 'application/json', 'X-Tracemine-Token': token }, body: body === undefined ? undefined : JSON.stringify(body) });
  if (!response.ok) {
    const data = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail));
  }
  return response.json();
}
export async function initialize() {
  const info = await api<{ token: string; example_repo: string }>('/info');
  token = info.token;
  return info;
}
