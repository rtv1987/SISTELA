import { useCallback, useEffect, useState } from 'react';
import { ArrowLeft, ArrowRight, Check, Copy, CheckCheck } from 'lucide-react';
import Decimal from 'decimal.js';
import type { Line } from './types';
import { typeLabel } from './types';

export const entryTarget = (line: Line) => {
  const c=line.review_data?.conversion;
  if(!c)return {quantity:line.quantity,unit:line.unit,valid:true};
  const valid=c.confirmed_by_user && new Decimal(c.source_quantity).eq(line.quantity) && c.source_unit===line.unit;
  return {quantity:c.target_quantity,unit:c.target_unit,valid};
};
export const plainQuantity = (value:string) => new Decimal(value.replace(',', '.')).toFixed();
const sameUnit=(a:string,b:string)=>a.toLowerCase().replace(/[.\s]/g,'')===b.toLowerCase().replace(/[.\s]/g,'');
export const entryReady = (line: Line) => (!line.review_data?.normative_unit || sameUnit(line.review_data.normative_unit,entryTarget(line).unit)) && !!line.unit && new Decimal(line.quantity).gt(0) && entryTarget(line).valid && (line.line_type !== 'Work' || !!line.sistela_code);
export const entryText = (line: Line) => [line.sistela_code, line.output_description, entryTarget(line).unit, plainQuantity(entryTarget(line).quantity)].map(s => s.replace(/[\r\n\t]+/g, ' ')).join('\t');

export function EntryMode({ lines, busy, onMark, onReview, worksOnly=false, onExit }: { lines: Line[]; worksOnly?: boolean; onExit?:()=>void; busy: boolean; onMark: (line: Line, entered: boolean) => Promise<void>; onReview: (id: string) => void }) {
  const [id, setId] = useState(''); const [copied, setCopied] = useState(''); const [error, setError] = useState(''); const [onlyPending, setOnlyPending] = useState(true); const [filter,setFilter]=useState('pending'); const [allTypes,setAllTypes]=useState(false);
  const scoped = worksOnly&&!allTypes?lines.filter(l=>l.line_type==='Work'):lines;
  const remaining = scoped.filter(l => !l.entered_at); const visible = (onlyPending ? remaining : scoped).filter(l=>filter==='review'?!entryReady(l):filter==='confirmed'?l.mapping_status==='confirmed':true);
  const index = Math.max(0, visible.findIndex(l => l.id === id)); const line = visible[index];
  const move = useCallback((delta: number) => { setId(visible[Math.max(0, Math.min(visible.length - 1, index + delta))]?.id || ''); setCopied(''); }, [index, visible]);
  const mark = useCallback(async () => { if (!line || busy || !entryReady(line)) return; try { await onMark(line, !line.entered_at); setCopied(''); } catch (e) { setError((e as Error).message); } }, [line, busy, onMark]);
  const copy = useCallback(async (text:string,key:string) => {try {await navigator.clipboard.writeText(text);setCopied(key);setError('');}catch{setError('Nepavyko pasiekti iškarpinės. Pažymėkite tekstą ir kopijuokite su Ctrl+C.');}},[]);
  useEffect(() => {const listener=(e:KeyboardEvent)=>{
    if(e.target instanceof HTMLElement && e.target.closest('input,textarea,select,[contenteditable="true"]'))return;
    if(e.altKey||e.metaKey||(e.ctrlKey&&e.key!=='Enter'))return;
    const key=e.key.toLowerCase();
    if(!['arrowright','arrowleft','enter',' ','c','q','d','escape'].includes(key))return;
    e.preventDefault();
    if(key==='arrowright')move(1);
    else if(key==='arrowleft')move(-1);
    else if(key==='escape')onExit?.();
    else if(line&&key==='c')void copy(line.sistela_code,'code');
    else if(line&&key==='q'&&entryTarget(line).valid)void copy(plainQuantity(entryTarget(line).quantity),'quantity');
    else if(line&&key==='d')void copy(line.output_description,'description');
    else if(key===' ')void mark();
    else if(key==='enter'&&line&&!busy&&entryReady(line)){
      const next=visible[index+1]?.id||'';
      void onMark(line,true).then(()=>{setId(next);}).catch(e=>setError(e.message));
    }
  };window.addEventListener('keydown',listener);return()=>window.removeEventListener('keydown',listener);},[move,mark,line,copy,onExit,busy,onMark,visible,index]);
  const completed = scoped.length - remaining.length;
  return <section className="entry-mode"><div className="entry-header"><div><p className="eyebrow">RANKINIS PERKĖLIMAS Į SISTELA</p><h2>Rankinis perkėlimas</h2><p>Neprivalomas atsarginis būdas. Kopijuokite reikšmes į SISTELA. Pažymėkite tik tada, kai patikrinote suvestą eilutę.</p></div><div className="entry-progress"><strong>{completed}<span> / {scoped.length}</span></strong><small>eilučių suvedėte · {scoped.length ? Math.round(completed/scoped.length*100) : 0}%</small><progress max={scoped.length || 1} value={completed}/></div></div>
    <div className="entry-controls"><label><input type="checkbox" checked={onlyPending} onChange={e => { setOnlyPending(e.target.checked);setFilter(e.target.checked?'pending':'all'); setId(''); }}/> Rodyti tik nesuvestas</label><select aria-label="Suvedimo filtras" value={filter} onChange={e=>{setFilter(e.target.value);setOnlyPending(e.target.value==='pending');setId('');}}><option value="pending">Nesuvesti darbai</option><option value="all">Visi darbai</option><option value="review">Reikia peržiūros</option><option value="confirmed">Tik patvirtinti</option></select>{worksOnly&&<label><input type="checkbox" checked={allTypes} onChange={e=>{setAllTypes(e.target.checked);setId('');}}/> Įtraukti medžiagas</label>}<span>← → · Enter – suvesti ir kita · C – kodas · Q – kiekis · D – tekstas · Space – žyma · Esc – išeiti</span>{onExit&&<button onClick={onExit}>Išeiti</button>}</div>
    {!line ? <div className="entry-complete"><CheckCheck size={38}/><h2>{lines.length ? 'Visos eilutės pažymėtos kaip suvestos' : 'Pirmiausia importuokite žiniaraštį'}</h2><p>Pažymėjimas reiškia jūsų patvirtinimą, ne automatinę patikrą SISTELA programoje.</p></div> : <div className="entry-card"><div className="entry-card-top"><span>{typeLabel[line.line_type]} · {line.system_type}</span><span>{index + 1} iš {visible.length} {line.entered_at && '· Suvesta'}</span></div><h3>{line.project_description}</h3>
      {!entryReady(line) && <div className="entry-warning">Prieš perkeldami įrašykite darbo kodą ir patikrinkite vienetą. <button onClick={() => onReview(line.id)}>Tikrinti lentelėje</button></div>}
      {([['Kodas', line.sistela_code || '', 'code'], ['Galutinis pavadinimas', line.output_description, 'description'], [`Projekto kiekis (${line.unit})`, plainQuantity(line.quantity), 'source'], ['Vienetas', entryTarget(line).unit, 'unit'], ['Kiekis', entryTarget(line).valid ? plainQuantity(entryTarget(line).quantity) : '', 'quantity']] as const).map(([label, value, key]) => <div className={`entry-field ${key}`} key={key}><label>{label}</label><output>{value || '—'}</output><button disabled={!value} onClick={() => void copy(value, key)} aria-label={`Kopijuoti: ${label}`}>{copied === key ? <Check size={16}/> : <Copy size={16}/>}</button></div>)}
      <div className="entry-note">{line.technical_reference && <span>Modelis: <strong>{line.technical_reference}</strong></span>}<span>Medžiagos kaina: {line.material_price ?? '—'} €</span><span>Darbo kaina: {line.work_price ?? '—'} €</span>{line.notes && <p>{line.notes}</p>}</div>
      <div className="entry-actions"><button onClick={() => move(-1)} disabled={index === 0}><ArrowLeft size={15}/> Ankstesnė</button><button disabled={!entryTarget(line).valid} onClick={() => void copy(entryText(line), 'row')}><Copy size={15}/>{copied === 'row' ? 'Nukopijuota' : 'Kopijuoti 4 laukus'}</button><button className="primary" onClick={() => void mark()} disabled={busy || !entryReady(line)}><Check size={16}/>{line.entered_at ? 'Grąžinti į nesuvestas' : 'Pažymėti suvestą'}</button><button onClick={() => move(1)} disabled={index >= visible.length - 1}>Kita<ArrowRight size={15}/></button></div>
      <p className="fine-print">Vienetai nekeičiami automatiškai: 100m ir m skiriasi. Kopijavimas nėra SISTELA paketo eksportas.</p>
    </div>}{error && <div role="alert" className="error-banner">{error}</div>}
  </section>;
}
