import './catalog-export.css';
import { useEffect, useState } from 'react';
import { api, post } from './api';

export interface CatalogEntry {id:string; code:string; description:string; unit:string; unit_id:string; category:string; kind:string; filename:string; record_number:number}
interface Source {id:string;label:string;active:boolean;fingerprint:string;diagnostics:{counts:Record<string,number>;unresolved_relations:number;unit_conflicts:Record<string,string[]>}}
export function Catalog({onUse}:{onUse?:(entry:CatalogEntry)=>Promise<void>}) {
  const [sources,setSources]=useState<Source[]>([]),[path,setPath]=useState(''),[query,setQuery]=useState('');
  const [kind,setKind]=useState('rate'),[unit,setUnit]=useState(''),[category,setCategory]=useState('');
  const [rows,setRows]=useState<CatalogEntry[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState('');
  const [detail,setDetail]=useState<unknown>(null);
  const refresh=()=>api<Source[]>('/normative/sources').then(setSources);
  useEffect(()=>{void refresh().catch(e=>setError(e.message));},[]);
  useEffect(()=>{let cancelled=false;const timer=setTimeout(()=>{void api<CatalogEntry[]>(`/normative/search?${new URLSearchParams({q:query,kind,unit,category})}`).then(r=>{if(!cancelled)setRows(r);}).catch(e=>{if(!cancelled)setError(e.message);});},200);return()=>{cancelled=true;clearTimeout(timer);};},[query,kind,unit,category,sources]);
  const run=async(job:()=>Promise<unknown>)=>{setBusy(true);setError('');try{await job();await refresh();}catch(e){setError((e as Error).message);}finally{setBusy(false);}};
  return <section className="info-panel catalog-panel"><h1>SISTELA normatyvinė bazė</h1><p>Vietinis katalogas. Originalūs DBF ir ZIP failai nekeičiami. Naudokite savo licencijuotą bazę.</p>
    <label>Normatyvų aplankas<input aria-label="Normatyvų aplankas" value={path} onChange={e=>setPath(e.target.value)}/></label>
    <button disabled={busy||!path.trim()} onClick={()=>void run(()=>post('/normative/folder',{path}))}>Importuoti / Atnaujinti katalogą</button>
    <label>Pasirinkti ZIP<input aria-label="Normatyvų ZIP" type="file" accept=".zip" disabled={busy} onChange={e=>{const file=e.target.files?.[0];if(file){const form=new FormData();form.set('file',file);void run(()=>api('/normative/zip',{method:'POST',body:form}));}e.target.value='';}}/></label>
    {busy&&<p role="status">Importuojama / išsaugoma…</p>}{error&&<p role="alert">{error}</p>}
    {sources.filter(s=>s.active).map(s=><div key={s.id}><strong>{s.label}</strong><p>{Object.entries(s.diagnostics.counts).map(([k,v])=>`${k}: ${v}`).join(' · ')}</p><details><summary>Katalogo kilmė ir neaiškumai</summary><p>SHA-256: {s.fingerprint}</p><p>Nesusieti ryšiai: {s.diagnostics.unresolved_relations}. Neaiškūs vienetai: {Object.keys(s.diagnostics.unit_conflicts).length}.</p></details></div>)}
    <div className="toolbar"><input aria-label="Ieškoti normatyvų" placeholder="Kodas arba pavadinimas" value={query} onChange={e=>setQuery(e.target.value)}/><select aria-label="Katalogo tipas" value={kind} onChange={e=>setKind(e.target.value)}><option value="rate">Darbai</option><option value="resource">Resursai</option><option value="resource_price">Medžiagų kainynas</option><option value="material">Gaminiai</option><option value="section">Skyriai</option><option value="text">Normatyvų tekstai</option></select><input aria-label="Katalogo vienetas" placeholder="Vienetas" value={unit} onChange={e=>setUnit(e.target.value)}/><input aria-label="Katalogo kategorija" placeholder="Kategorija / rinkinys" value={category} onChange={e=>setCategory(e.target.value)}/></div>
    <table><thead><tr><th>Kodas</th><th>Normatyvo pavadinimas</th><th>Vienetas</th><th>Veiksmas</th></tr></thead><tbody>{rows.map(r=><tr key={r.id}><td>{r.code}</td><td>{r.description}<small>{r.category}</small></td><td>{r.unit||`Nežinomas (${r.unit_id})`}</td><td><button disabled={busy} onClick={()=>void api(`/normative/entries/${r.id}`).then(setDetail).catch(e=>setError(e.message))}>Šaltinis ir resursai</button>{onUse&&<button disabled={busy} onClick={()=>void run(()=>onUse(r))}>Naudoti projekte</button>}</td></tr>)}</tbody></table>
    {detail!==null&&<details open><summary>Šaltinio duomenys</summary><pre>{JSON.stringify(detail,null,2)}</pre></details>}
  </section>;
}
