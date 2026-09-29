import { useEffect, useState } from 'react';
import { Check, ArrowDown } from 'lucide-react';
import { api } from './api';
import { type Line, type Suggestion } from './types';
export function MappingPanel({ line, busy, onApply, onConfirm }: { line: Line; busy: boolean; onApply: (s: Suggestion) => Promise<void>; onConfirm: (code: string, original: string, unit: string) => Promise<void> }) {
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [code, setCode] = useState(line.sistela_code); const [original, setOriginal] = useState(line.sistela_original_description); const [unit, setUnit] = useState(line.unit); const [error, setError] = useState('');
  useEffect(() => { setCode(line.sistela_code); setOriginal(line.sistela_original_description); setUnit(line.unit); setError(''); let cancelled = false;
    void api<Suggestion[]>(`/projects/${line.project_id}/lines/${line.id}/suggestions`).then(s => { if (!cancelled) setSuggestions(s); }).catch(e => { if (!cancelled) setError(e.message); }); return () => { cancelled = true; };
  }, [line.id, line.version, line.project_id, line.sistela_code, line.sistela_original_description, line.unit]);
  if (line.line_type !== 'Work') return <div className="mapping-material"><Check size={16}/><p>Medžiagos eilutė.<br/>Darbų normatyvas nepriskiriamas.</p></div>;
  return <div className="mapping-panel"><div className="panel-kicker">NORMATYVO PARINKIMAS</div>
    {suggestions.length > 0 ? suggestions.map(s => <div key={s.mapping_id} className="suggestion"><div><strong>{s.sistela_code}</strong><span className={`confidence ${Number(s.confidence) >= .9 ? 'high' : Number(s.confidence) >= .7 ? 'medium' : 'low'}`}>{Math.round(Number(s.confidence) * 100)} %</span></div><p>{s.sistela_description || 'Originalus pavadinimas nežinomas'}</p><small>{s.method === 'exact' ? 'Tikslus tekstas' : s.method === 'normalized' ? 'Normalizuotas tekstas' : 'Panašus tekstas'} · {s.confirmed_count} patvirtinimai · {s.source_unit}</small><button disabled={!s.compatible || busy} onClick={() => void onApply(s).catch(() => {})}><ArrowDown size={13}/> Pritaikyti pasiūlymą</button>{!s.compatible && <p className="error-text">Skiriasi vienetai. Kiekį reikia perskaičiuoti rankiniu būdu.</p>}</div>) : <p className="muted">Patvirtintų atitikmenų dar nėra. Pasirinkite kodą SISTELA programoje – šį pasirinkimą prisiminsime.</p>}
    <form onSubmit={e => { e.preventDefault(); void onConfirm(code, original, unit).catch(() => {}); }}><label>SISTELA normatyvo kodas<input aria-label="Patvirtinamas SISTELA kodas" value={code} onChange={e => setCode(e.target.value)} required/></label><label>Originalus normatyvo pavadinimas<textarea aria-label="Originalus normatyvo pavadinimas" placeholder="Jei žinomas. Galutinio teksto nekeičia." value={original} onChange={e => setOriginal(e.target.value)}/></label><label>Patikrintas normatyvo vienetas<input aria-label="Normatyvo vienetas" value={unit} onChange={e => setUnit(e.target.value)} required/></label><button className="primary" disabled={busy || !code.trim()} type="submit"><Check size={14}/> Patvirtinti pasirinkimą</button></form>
    {line.mapping_status === 'confirmed' && <p className="confirmation-note"><Check size={13}/> Pasirinkimas patvirtintas ir išsaugotas istorijoje.</p>}
    <p className="fine-print">Atitikimo įvertis yra pagalbinis signalas, ne tikimybė. Galutinis pavadinimas lieka jūsų.</p>{error && <p className="error-text">{error}</p>}
  </div>;
}
