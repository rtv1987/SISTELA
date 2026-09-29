import { useEffect, useState } from 'react';
import { Check, Database, Search, Upload, X } from 'lucide-react';
import { api, post } from './api';

export interface HistoricalLine {
  id: string; version: number; description: string; sistela_code: string; unit: string;
  quantity: string | null; historical_price: string | null; system_type: string;
  status: 'CANDIDATE' | 'CONFIRMED' | 'REJECTED' | 'NOT_APPLICABLE';
  evidence_type: 'DIRECT' | 'DERIVED' | 'AMBIGUOUS'; bulk_eligible: boolean;
  estimate_name: string; project_name: string; section_name: string; line_type: string;
  system_evidence: string; source_date: string | null;
}
interface HistoricalImport {
  id: string; source_reference: string; imported_at: string; line_count: number; work_count: number;
  confirmed_count: number; rejected_count: number; warning_count: number; warnings: {message:string}[];
  estimates: {id:string; name:string; project_name:string; system_type:string}[];
}
interface Evidence extends HistoricalLine {
  imported_at: string; evidence: {description_kind: string; header?: {file:string; record:number; sha256:string; fields:Record<string,unknown>}; parents?: unknown[]; section?:unknown[]};
  reviews: {status:string; previous_status:string; created_at:string; system_type:string}[];
}
const statuses = {CANDIDATE:'Kandidatas',CONFIRMED:'Patvirtinta',REJECTED:'Atmesta',NOT_APPLICABLE:'Medžiaga'};
const systems = ['GSS','AS','VS','IK','ER','LER'];
const quality = {DIRECT:'Tiesioginis įrašas',DERIVED:'Patikrinta jungtis',AMBIGUOUS:'Neaiški jungtis'};

export function EvidenceDrawer({id, onClose}: {id:string; onClose:()=>void}) {
  const [data,setData] = useState<Evidence|null>(null), [error,setError] = useState('');
  useEffect(() => { let cancelled=false; setData(null); setError('');
    void api<Evidence>(`/history/lines/${id}/evidence`).then(value => {if(!cancelled) setData(value);}).catch(e => {if(!cancelled) setError(e.message);});
    return () => {cancelled=true;}; },[id]);
  useEffect(() => { const close=(e:KeyboardEvent) => {if(e.key==='Escape') onClose();}; window.addEventListener('keydown',close); return () => window.removeEventListener('keydown',close); },[onClose]);
  return <div className="history-overlay"><section className="evidence-drawer" role="dialog" aria-modal="true" aria-label="Istorinio pasiūlymo įrodymai"><header><div><p className="eyebrow">IŠ KUR ŠIS PASIŪLYMAS?</p><h2>Istorinis įrodymas</h2></div><button autoFocus aria-label="Uždaryti įrodymus" onClick={onClose}><X size={18}/></button></header>
    {error && <p role="alert">{error}</p>}{!data && !error && <p>Skaitoma…</p>}
    {data && <><div className="evidence-code">{data.sistela_code}<span className={`status ${data.status.toLowerCase()}`}>{statuses[data.status]}</span></div><h3>{data.description}</h3><p className="muted">Istorinis išvesties pavadinimas. Originalus katalogo pavadinimas nežinomas.</p>
      <dl className="evidence-facts"><dt>Projektas / objektas</dt><dd>{data.project_name}</dd><dt>Sąmata</dt><dd>{data.estimate_name}</dd><dt>Skyrius</dt><dd>{data.section_name || 'Nežinomas'}</dd><dt>Sistema</dt><dd>{data.system_type || 'Nepriskirta'} · {data.status==='CONFIRMED'?'patvirtinta žmogaus':'pagal sąmatos pavadinimą – patikrinkite'}</dd><dt>Kiekis ir vienetas</dt><dd>{data.quantity ?? '—'} {data.unit || 'Nežinomas'}</dd><dt>Įrodymo kokybė</dt><dd>{quality[data.evidence_type]}</dd><dt>Importuota</dt><dd>{data.imported_at.slice(0,10)}</dd><dt>Archyve įrašyta data</dt><dd>{data.source_date || 'Nežinoma'} (tai nėra patvirtinta panaudojimo data)</dd></dl>
      <div className="history-note">Archyvo kainos reikšmė: {data.historical_price ?? '—'}. Jos semantika ir aktualumas nepatvirtinti; dabartinės kainos nekeičiamos.</div>
      <h3>Šaltinis</h3><p>{data.evidence.header?.file} · įrašas {data.evidence.header?.record}</p><p className="muted">{data.evidence_type==='DERIVED'?'sd ir dd pozicijos sutampa pagal 8 laukų raktą, kodą bei kiekį.':data.evidence_type==='DIRECT'?'Aprašymas ir kodas pateikti tame pačiame dd įraše.':'Jungtis neaiški. Peržiūrėkite visus įrašus prieš patvirtindami.'}</p>
      <details><summary>Techninis atsekamumas</summary><pre>{JSON.stringify(data.evidence,null,2)}</pre></details>
      <h3>Peržiūros istorija</h3>{data.reviews.length?data.reviews.map((r,i)=><p key={i}>{r.created_at.slice(0,16).replace('T',' ')} · {r.previous_status} → {r.status} · {r.system_type}</p>):<p className="muted">Žmogaus patvirtinimo dar nėra.</p>}</>}
  </section></div>;
}

export function HistoryScreen() {
  const [imports,setImports]=useState<HistoricalImport[]>([]),[importId,setImportId]=useState('');
  const [rows,setRows]=useState<HistoricalLine[]>([]),[total,setTotal]=useState(0),[offset,setOffset]=useState(0);
  const [search,setSearch]=useState(''),[system,setSystem]=useState(''),[code,setCode]=useState(''),[status,setStatus]=useState('CANDIDATE');
  const [encoding,setEncoding]=useState('cp1257'),[busy,setBusy]=useState(false),[loading,setLoading]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  const [refresh,setRefresh]=useState(0),[selected,setSelected]=useState<string[]>([]),[evidence,setEvidence]=useState('');
  const [reviewing,setReviewing]=useState<HistoricalLine|null>(null),[reviewSystem,setReviewSystem]=useState(''),[acknowledge,setAcknowledge]=useState(false);
  useEffect(()=> {let cancelled=false; void api<HistoricalImport[]>('/history/imports').then(value=>{if(!cancelled)setImports(value);}).catch(e=>{if(!cancelled)setError(e.message);});return()=>{cancelled=true;};},[refresh]);
  useEffect(()=> {let cancelled=false; setLoading(true);setSelected([]);
    const params=new URLSearchParams({search,system,code,status,limit:'100',offset:String(offset)});if(importId)params.set('import_id',importId);
    void api<{items:HistoricalLine[];total:number}>(`/history/lines?${params}`).then(value=>{if(!cancelled){setRows(value.items);setTotal(value.total);}}).catch(e=>{if(!cancelled)setError(e.message);}).finally(()=>{if(!cancelled)setLoading(false);});
    return()=>{cancelled=true;};},[importId,search,system,code,status,offset,refresh]);
  const filter=(set:(value:string)=>void)=>(value:string)=>{set(value);setOffset(0);};
  async function upload(files:FileList) {setBusy(true);setError('');setNotice('');try{const form=new FormData();Array.from(files).forEach(f=>form.append('files',f));form.set('encoding',encoding);
    const result=await api<HistoricalImport & {duplicate:boolean}>('/history/imports',{method:'POST',body:form});setImportId(result.id);setOffset(0);setRefresh(v=>v+1);
    setNotice(result.duplicate?'Šis archyvas jau importuotas. Duomenys nesidubliavo.':`Importuota: ${result.estimates.length} sąmatos, ${result.line_count} eilutės, ${result.work_count} darbų kandidatų.`);
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  async function review(items:HistoricalLine[],nextStatus:'CONFIRMED'|'REJECTED',override?:string) {setBusy(true);setError('');try{
    await post('/history/review',{items:items.map(r=>({id:r.id,version:r.version,system_type:override || r.system_type || null})),status:nextStatus,acknowledge_ambiguity:items.length===1 && acknowledge});
    setNotice(`${items.length} kandidatų: ${nextStatus==='CONFIRMED'?'patvirtinta':'atmesta'}.`);setReviewing(null);setSelected([]);setOffset(0);setRefresh(v=>v+1);
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  const chosen=rows.filter(r=>selected.includes(r.id));const current=imports.find(i=>i.id===importId);
  return <section className="history-screen"><div className="project-title"><div><p className="eyebrow">VIETINĖ DARBŲ KODŲ ISTORIJA</p><h1>Istorinės SISTELA sąmatos</h1><p className="muted">Ankstesni pasirinkimai su patikrinamu šaltiniu. Kandidatas nėra patvirtintas normatyvas.</p></div><Database size={32}/></div>
    <div className="history-upload"><div><strong>Importuoti DBF archyvą</strong><p>Pasirinkite to paties rinkinio sd, dd, nd ir turimus pd, td, od failus. Iki 25 MB. Tik skaitymas.</p></div><label>Koduotė<select aria-label="DBF koduotė" value={encoding} disabled={busy} onChange={e=>setEncoding(e.target.value)}><option value="cp1257">cp1257 (pateiktas archyvas)</option><option value="cp1252">cp1252</option><option value="utf-8">UTF-8</option></select></label><label className="button history-file"><Upload size={16}/>{busy?'Apdorojama…':'Pasirinkti DBF failus'}<input aria-label="DBF archyvo failai" type="file" accept=".dbf" multiple disabled={busy} onChange={e=>{if(e.target.files?.length)void upload(e.target.files);e.target.value='';}}/></label></div>
    {error&&<div role="alert" className="error-banner">{error}</div>}{notice&&<div role="status" className="history-notice"><Check size={16}/>{notice}</div>}
    <div className="history-imports"><button className={!importId?'current':''} onClick={()=>filter(setImportId)('')}>Visi archyvai <strong>{imports.length}</strong></button>{imports.map(item=><button key={item.id} className={importId===item.id?'current':''} onClick={()=>filter(setImportId)(item.id)}><strong className="historical-project">{item.estimates[0]?.project_name || item.source_reference}</strong><span>{item.estimates.length} sąmatos · {item.work_count} darbų · {item.confirmed_count} patvirtinta</span><small>Importuota {item.imported_at.slice(0,10)}</small></button>)}</div>
    {current&&<div className="history-note">{current.estimates.map(e=>`${e.system_type||'?'}: ${e.name}`).join(' · ')}{current.warning_count>0&&<details><summary>{current.warning_count} įspėjimai</summary>{current.warnings.map((w,i)=><p key={i}>{w.message}</p>)}</details>}</div>}
    <div className="history-filters"><label><Search size={15}/><input aria-label="Ieškoti istorijoje" placeholder="Aprašymo paieška…" value={search} onChange={e=>filter(setSearch)(e.target.value)}/></label><select aria-label="Istorijos sistema" value={system} onChange={e=>filter(setSystem)(e.target.value)}><option value="">Visos sistemos</option>{[...new Set([...systems,system,...rows.map(r=>r.system_type)])].filter(Boolean).map(s=><option key={s}>{s}</option>)}</select><input aria-label="Istorijos SISTELA kodas" placeholder="SISTELA kodas" value={code} onChange={e=>filter(setCode)(e.target.value)}/><select aria-label="Istorijos būsena" value={status} onChange={e=>filter(setStatus)(e.target.value)}><option value="">Visos būsenos</option>{Object.entries(statuses).map(([v,label])=><option key={v} value={v}>{label}</option>)}</select><span>{total} rezultatų</span></div>
    <div className="history-bulk"><button disabled={busy||loading||!chosen.length||chosen.some(r=>!r.bulk_eligible)} onClick={()=>void review(chosen,'CONFIRMED')}><Check size={15}/> Patvirtinti pažymėtus ({chosen.length})</button><span>Masinis patvirtinimas galimas tik aiškiems darbų kandidatams su sistema ir vienetu.</span></div>
    <div className="history-table-wrap" aria-busy={loading}><table className="history-table"><thead><tr><th>✓</th><th>Istorinis aprašymas / sąmata</th><th>Sistema</th><th>Vienetas</th><th>SISTELA kodas</th><th>Įrodymas / būsena</th><th>Peržiūra</th></tr></thead><tbody>{rows.map(row=><tr key={row.id}><td><input type="checkbox" aria-label={`Pažymėti kandidatą ${row.sistela_code} ${row.id}`} disabled={!row.bulk_eligible||loading||busy} checked={selected.includes(row.id)} onChange={e=>setSelected(previous=>e.target.checked?[...previous,row.id]:previous.filter(id=>id!==row.id))}/></td><td><strong>{row.description||'Aprašymas nežinomas'}</strong><small>{row.estimate_name} · {row.section_name||'Skyrius nežinomas'}</small></td><td>{row.system_type||'Nepriskirta'}</td><td>{row.unit||'?'}</td><td><code>{row.sistela_code||'?'}</code></td><td><span className={`status ${row.status.toLowerCase()}`}>{statuses[row.status]}</span><small>{quality[row.evidence_type]}</small></td><td><button aria-label={`Įrodymai ${row.sistela_code}`} onClick={()=>setEvidence(row.id)}>Įrodymai</button>{row.status!=='NOT_APPLICABLE'&&<><button disabled={busy||loading} onClick={()=>{setReviewing(row);setReviewSystem(row.system_type);setAcknowledge(false);}}>Peržiūrėti</button><button disabled={busy||loading||row.status==='REJECTED'} onClick={()=>void review([row],'REJECTED')}>Atmesti</button></>}</td></tr>)}</tbody></table>{!rows.length&&<div className="empty-grid">{loading?'Skaitoma istorija…':'Pagal filtrus kandidatų nėra. Importuokite DBF archyvą arba pakeiskite filtrus.'}</div>}</div>
    <div className="history-pagination"><button disabled={offset===0||loading} onClick={()=>setOffset(v=>Math.max(0,v-100))}>Ankstesni</button><span>{total?offset+1:0}–{Math.min(offset+100,total)} iš {total}</span><button disabled={offset+100>=total||loading} onClick={()=>setOffset(v=>v+100)}>Kiti</button></div>
    {reviewing&&<div className="history-overlay"><section className="history-review" role="dialog" aria-modal="true" aria-label="Patvirtinti istorinį kandidatą"><header><h2>Patikrinkite pasirinkimą</h2><button aria-label="Uždaryti peržiūrą" onClick={()=>setReviewing(null)}><X size={18}/></button></header><h3>{reviewing.sistela_code} · {reviewing.description}</h3><p>{reviewing.estimate_name} · {reviewing.unit} · {quality[reviewing.evidence_type]}</p><label>Sistema (patikrinkite numanomą reikšmę)<input aria-label="Patvirtinama istorijos sistema" value={reviewSystem} onChange={e=>setReviewSystem(e.target.value)} list="history-systems" maxLength={100}/><datalist id="history-systems">{systems.map(s=><option key={s} value={s}/>)}</datalist></label><p className="muted">Patvirtinate istorinį kodo pasirinkimą. Originalus katalogo pavadinimas ir dabartinės kainos nekeičiami.</p>{reviewing.evidence_type==='AMBIGUOUS'&&<label><input type="checkbox" checked={acknowledge} onChange={e=>setAcknowledge(e.target.checked)}/> Peržiūrėjau neaiškią jungtį ir savarankiškai patikrinau šį kodą bei vienetą.</label>}<div className="excel-actions"><button onClick={()=>setEvidence(reviewing.id)}>Peržiūrėti įrodymus</button><button className="primary" disabled={busy||!reviewSystem.trim()||!reviewing.unit||!reviewing.sistela_code||(reviewing.evidence_type==='AMBIGUOUS'&&!acknowledge)} onClick={()=>void review([reviewing],'CONFIRMED',reviewSystem)}>Patvirtinti kandidatą</button></div></section></div>}
    {evidence&&<EvidenceDrawer id={evidence} onClose={()=>setEvidence('')}/>}
  </section>;
}
