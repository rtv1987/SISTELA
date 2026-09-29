import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Copy, CheckCheck } from 'lucide-react';
import type { Line } from './types';
import { typeLabel } from './types';

export const entryReady = (line: Line) => !!line.unit && (line.line_type !== 'Work' || (line.mapping_status === 'confirmed' && !!line.sistela_code));
export const entryText = (line: Line) => [line.sistela_code, line.output_description, line.unit, line.quantity].map(s => s.replace(/[\r\n\t]+/g, ' ')).join('\t');

export function EntryMode({ lines, busy, onMark, onReview }: { lines: Line[]; busy: boolean; onMark: (line: Line, entered: boolean) => Promise<void>; onReview: (id: string) => void }) {
  const [id, setId] = useState(''); const [copied, setCopied] = useState(''); const [error, setError] = useState(''); const [onlyPending, setOnlyPending] = useState(true);
  const remaining = lines.filter(l => !l.entered_at); const visible = onlyPending ? remaining : lines;
  const index = Math.max(0, visible.findIndex(l => l.id === id)); const line = visible[index];
  const move = useCallback((delta: number) => { setId(visible[Math.max(0, Math.min(visible.length - 1, index + delta))]?.id || ''); setCopied(''); }, [index, visible]);
  const mark = useCallback(async () => { if (!line || busy || !entryReady(line)) return; try { await onMark(line, !line.entered_at); setCopied(''); } catch (e) { setError((e as Error).message); } }, [line, busy, onMark]);
  useEffect(() => { const listener = (e: KeyboardEvent) => { if (e.target instanceof HTMLElement && e.target.closest('input,textarea,select')) return; if (e.key === 'ArrowRight') { e.preventDefault(); move(1); } if (e.key === 'ArrowLeft') { e.preventDefault(); move(-1); } if (e.ctrlKey && e.key === 'Enter') { e.preventDefault(); void mark(); } }; window.addEventListener('keydown', listener); return () => window.removeEventListener('keydown', listener); }, [move, mark]);
  async function copy(text: string, key: string) { try { await navigator.clipboard.writeText(text); setCopied(key); setError(''); } catch { setError('Nepavyko pasiekti iškarpinės. Pažymėkite tekstą ir kopijuokite su Ctrl+C.'); } }
  const completed = lines.length - remaining.length;
  return <section className="entry-mode"><div className="entry-header"><div><p className="eyebrow">RANKINIS PERKĖLIMAS Į SISTELA</p><h2>Viena eilutė. Visi reikalingi laukai.</h2><p>Kopijuokite reikšmes į SISTELA. Pažymėkite tik tada, kai patikrinote suvestą eilutę.</p></div><div className="entry-progress"><strong>{completed}<span> / {lines.length}</span></strong><small>eilučių suvedėte</small><progress max={lines.length || 1} value={completed}/></div></div>
    <div className="entry-controls"><label><input type="checkbox" checked={onlyPending} onChange={e => { setOnlyPending(e.target.checked); setId(''); }}/> Rodyti tik nesuvestas</label><span>← → – eilutės · Ctrl+Enter – pažymėti suvestą</span></div>
    {!line ? <div className="entry-complete"><CheckCheck size={38}/><h2>{lines.length ? 'Visos eilutės pažymėtos kaip suvestos' : 'Pirmiausia importuokite žiniaraštį'}</h2><p>Pažymėjimas reiškia jūsų patvirtinimą, ne automatinę patikrą SISTELA programoje.</p></div> : <div className="entry-card"><div className="entry-card-top"><span>{typeLabel[line.line_type]} · {line.system_type}</span><span>{index + 1} iš {visible.length} {line.entered_at && '· Suvesta'}</span></div><h3>{line.project_description}</h3>
      {!entryReady(line) && <div className="entry-warning">Prieš perkeldami patvirtinkite darbo normatyvą ir vienetą. <button onClick={() => onReview(line.id)}>Tikrinti lentelėje</button></div>}
      {([['Kodas', line.sistela_code || '', 'code'], ['Galutinis pavadinimas', line.output_description, 'description'], ['Vienetas', line.unit, 'unit'], ['Kiekis', line.quantity, 'quantity']] as const).map(([label, value, key]) => <div className={`entry-field ${key}`} key={key}><label>{label}</label><output>{value || '—'}</output><button disabled={!value} onClick={() => void copy(value, key)} aria-label={`Kopijuoti: ${label}`}>{copied === key ? <Check size={16}/> : <Copy size={16}/>}</button></div>)}
      <div className="entry-note">{line.technical_reference && <span>Modelis: <strong>{line.technical_reference}</strong></span>}<span>Medžiagos kaina: {line.material_price ?? '—'} €</span><span>Darbo kaina: {line.work_price ?? '—'} €</span>{line.notes && <p>{line.notes}</p>}</div>
      <div className="entry-actions"><button onClick={() => move(-1)} disabled={index === 0}><ArrowLeft size={15}/> Ankstesnė</button><button onClick={() => void copy(entryText(line), 'row')}><Copy size={15}/>{copied === 'row' ? 'Nukopijuota' : 'Kopijuoti 4 laukus'}</button><button className="primary" onClick={() => void mark()} disabled={busy || !entryReady(line)}><Check size={16}/>{line.entered_at ? 'Grąžinti į nesuvestas' : 'Pažymėti suvestą'}</button><button onClick={() => move(1)} disabled={index >= visible.length - 1}>Kita<ArrowRight size={15}/></button></div>
      <p className="fine-print">Vienetai nekeičiami automatiškai: 100m ir m skiriasi. Kopijavimas nėra SISTELA paketo eksportas.</p>
    </div>}{error && <div role="alert" className="error-banner">{error}</div>}
  </section>;
}
