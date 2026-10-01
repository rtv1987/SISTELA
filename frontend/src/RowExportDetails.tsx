import { useEffect, useState } from 'react';
import { api } from './api';
import type { Line } from './types';

export function RowExportDetails({line,onSaved}:{line:Line;onSaved:(line:Line)=>Promise<void>}){
  const [mark,setMark]=useState('S'),[ngr,setNgr]=useState(12),[parameters,setParameters]=useState(''),[error,setError]=useState('');
  useEffect(()=>{const o=line.review_data?.export_options;setMark(o?.mark||(line.line_type==='Equipment'?'I':'S'));setNgr(o?.ngr||12);setParameters(o?.parameters?.join(',')||'');},[line]);
  async function save(){try{const row=await api<Line>(`/projects/${line.project_id}/lines/${line.id}/export-options`,{method:'PUT',body:JSON.stringify({version:line.version,options:{...line.review_data?.export_options,mark,ngr,parameters:parameters?parameters.split(',').map(Number):null}})});await onSaved(row);setError('');}catch(e){setError((e as Error).message);}}
  return <details><summary>Papildomi eilutės eksporto duomenys</summary><label>Žymė<select aria-label="Eilutės žymė" value={mark} onChange={e=>setMark(e.target.value)}><option>S</option><option>I</option><option>G</option></select></label><label>NGR grupė<select aria-label="Eilutės NGR" value={ngr} onChange={e=>setNgr(Number(e.target.value))}>{['Metalas','Vamzdžiai','Bendrosios statybinės','Apdailos','Elektrotechninės','Santechninės','Langai / durys','Mediena','Izoliacija','Betonas','Pusfabrikačiai','Kitos medžiagos'].map((n,i)=><option key={n} value={i+1}>{i+1} · {n}</option>)}</select></label><label>Parametrinio įkainio G<input aria-label="Eilutės G" value={parameters} onChange={e=>setParameters(e.target.value)}/></label><button onClick={()=>void save()}>Išsaugoti eilutės duomenis</button>{error&&<p role="alert">{error}</p>}</details>;
}
