import { KnowledgeEntry, MetaPayload, Paper, SearchPayload, SearchRequest } from './types';

const API_BASE = '';

async function parseError(response: Response): Promise<Error> {
  const text = await response.text();
  try {
    const data = JSON.parse(text);
    const detail = data.detail;
    if (typeof detail === 'string') return new Error(detail);
    if (detail?.message) return new Error(detail.message);
    if (detail?.raw_error) return new Error(detail.raw_error);
  } catch {
    if (text) return new Error(text);
  }
  return new Error(`Request failed with status ${response.status}`);
}

export async function searchPapers(request: SearchRequest): Promise<SearchPayload> {
  const response = await fetch(`${API_BASE}/api/search`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export async function getMeta(): Promise<MetaPayload> {
  const response = await fetch(`${API_BASE}/api/meta`);
  if (!response.ok) throw await parseError(response);
  return response.json();
}

export async function updatePaperStatus(paperId: string, status: string): Promise<void> {
  const response = await fetch(`${API_BASE}/api/status`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper_id: paperId, status }),
  });
  if (!response.ok) throw await parseError(response);
}

export async function saveKnowledgeEntry(paper: Paper, note: string, tags: string[], keyTakeaways: string[]): Promise<KnowledgeEntry> {
  const response = await fetch(`${API_BASE}/api/knowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ paper, note, tags, key_takeaways: keyTakeaways }),
  });
  if (!response.ok) throw await parseError(response);
  const data = await response.json();
  return data.entry;
}

export async function exportPayload(payload: SearchPayload, exportFormat: string): Promise<string> {
  const response = await fetch(`${API_BASE}/api/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ payload, export_format: exportFormat }),
  });
  if (!response.ok) throw await parseError(response);
  const data = await response.json();
  return data.path;
}
