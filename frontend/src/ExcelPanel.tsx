import { useState } from 'react';
import { Upload, ClipboardPaste, X } from 'lucide-react';
import Decimal from 'decimal.js';
import { api } from './api';
import { blankLine } from './types';

interface Preview { sheets: {name: string; rows: number}[]; sheet: string; header_row: number; mapping: Record<string, number>; fields: Record<string, string>; columns: {index: number; label: string}[]; preview: (string | null)[][] }

export function parseTsv(text: string): string[][] {
  const rows: string[][] = []; let row: string[] = [], value = '', quoted = false;
  for (let i = 0; i < text.length; i++) { const char = text[i];
    if (char === '"' && (quoted || value === '')) { if (quoted && text[i+1] === '"') { value += '"'; i++; } else quoted = !quoted; }
    else if (!quoted && char === '\t') { row.push(value); value = ''; }
    else if (!quoted && (char === '\r' || char === '\n')) { if (char === '\r' && text[i+1] === '\n') i++; row.push(value); if (row.some(v => v.trim())) rows.push(row); row = []; value = ''; }
    else value += char;
  }
  if (quoted) throw new Error('Neuždarytos kabutės įklijuotame tekste.');
  row.push(value); if (row.some(v => v.trim())) rows.push(row);
  return rows;
}

export function pasteLines(text: string, system: string) {
  const rows = parseTsv(text); if (!rows.length || rows.length > 500) throw new Error('Įklijuokite nuo 1 iki 500 eilučių.');
  return rows.map((row, i) => { if (row.length !== 3) throw new Error(`${i+1} eilutėje turi būti 3 kolonos: pavadinimas, vienetas, kiekis.`);
    const [description, unit, raw] = row.map(v => v.trim());
    const normalized = raw.replace(',', '.');
    if (!description || !unit || !/^\d+(?:\.\d{1,6})?$/.test(normalized) || !new Decimal(normalized).isFinite()) throw new Error(`${i+1} eilutė: patikrinkite pavadinimą, vienetą ir kiekį.`);
    return { ...blankLine(system), project_description: description, output_description: description, unit, quantity: normalized };
  });
}

export function ExcelPanel({ system, busy, onClose, onImport, onPaste }: { system: string; busy: boolean; onClose: () => void; onImport: (form: FormData) => Promise<void>; onPaste: (rows: ReturnType<typeof pasteLines>) => Promise<void> }) {
  const [file, setFile] = useState<File | null>(null); const [preview, setPreview] = useState<Preview | null>(null);
  const [mapping, setMapping] = useState<Record<string, number>>({}); const [header, setHeader] = useState(1);
  const [loading, setLoading] = useState(false); const [error, setError] = useState(''); const [partial, setPartial] = useState(false); const [paste, setPaste] = useState('');
  async function inspect(chosen: File, sheet = '', row = 0) { setLoading(true); setError(''); try { const form = new FormData(); form.set('file', chosen); form.set('sheet', sheet); form.set('header_row', String(row)); const result = await api<Preview>('/xlsx/preview', { method:'POST', body:form }); setPreview(result); setHeader(result.header_row); setMapping(result.mapping); setFile(chosen); } catch (e) { setError((e as Error).message); setPreview(null); } finally { setLoading(false); } }
  async function submit() { if (!file || !preview) return; const form = new FormData(); form.set('file', file); form.set('sheet', preview.sheet); form.set('header_row', String(header)); form.set('mapping', JSON.stringify(mapping)); form.set('allow_partial', String(partial)); try { await onImport(form); } catch (e) { setError((e as Error).message); } }
  return <section className="info-panel"><div className="panel-heading"><h3>Excel importas ir įklijavimas</h3><button aria-label="Uždaryti Excel importą" onClick={onClose}><X size={17}/></button></div><div className="excel-form">
    <div className="excel-options"><label>XLSX failas<input type="file" aria-label="XLSX failas" accept=".xlsx" disabled={loading || busy} onChange={e => { if (e.target.files?.[0]) void inspect(e.target.files[0]); }}/></label>
    {preview && <><label>Darbo lapas<select aria-label="Darbo lapas" value={preview.sheet} disabled={loading || busy} onChange={e => file && void inspect(file, e.target.value)}>{preview.sheets.map(s => <option key={s.name}>{s.name}</option>)}</select></label><label>Antraštės eilutė<input type="number" min="1" max="10000" aria-label="Antraštės eilutė" value={header} onChange={e => setHeader(Number(e.target.value))}/></label><button disabled={loading || busy} onClick={() => file && void inspect(file, preview.sheet, header)}>Atpažinti kolonas</button></>}</div>
    {loading && <p>Skaitomas vietinis failas…</p>}
    {preview && <><div className="column-mapping">{Object.entries(preview.fields).map(([field, label]) => <label key={field}>{label}<select aria-label={`Kolona: ${label}`} value={mapping[field] ?? ''} onChange={e => setMapping(previous => { const next = { ...previous }; if (e.target.value === '') delete next[field]; else next[field] = Number(e.target.value); return next; })}><option value="">Nenaudoti</option>{preview.columns.map(c => <option key={c.index} value={c.index}>{c.label}</option>)}</select></label>)}</div>
      <div style={{overflowX:'auto'}}><table className="preview-table"><thead><tr>{preview.columns.map(c => <th key={c.index}>{c.label}</th>)}</tr></thead><tbody>{preview.preview.map((row,i) => <tr key={i}>{row.map((value,j) => <td key={j}>{value}</td>)}</tr>)}</tbody></table></div>
      <label className="muted"><input type="checkbox" checked={partial} onChange={e => setPartial(e.target.checked)}/> Leisti dalinį importą: netinkamos eilutės bus praleistos ir nurodytos importo informacijoje.</label>
      <div className="excel-actions"><button className="primary" disabled={busy || loading || !['project_description','unit','quantity'].every(f => f in mapping)} onClick={() => void submit()}><Upload size={15}/> Importuoti pasirinktą lapą</button><span className="muted">Kodus reikia patvirtinti. Formulės nevykdomos.</span></div></>}
    <details><summary>Įklijuoti iš Excel (3 kolonos)</summary><p className="muted">Pavadinimas → vienetas → kiekis. Be antraštės. Taip pat galite įklijuoti tiesiai į darbo lentelę.</p><textarea aria-label="Excel įklijavimas" className="paste-text" value={paste} onChange={e => setPaste(e.target.value)} placeholder={'Kabelis\tm\t650'}/><button disabled={busy || !paste.trim()} onClick={() => { try { void onPaste(pasteLines(paste, system)).then(() => setPaste('')).catch(e => setError(e.message)); } catch (e) { setError((e as Error).message); } }}><ClipboardPaste size={15}/> Pridėti įklijuotas eilutes</button></details>
    {error && <div role="alert" className="excel-warning">{error}</div>}
  </div></section>;
}
