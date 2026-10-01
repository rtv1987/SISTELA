import { useState } from 'react';
import { api, apiUrl } from './api';

export function DbfExport({projectId}:{projectId:string}) {
  const [open,setOpen]=useState(false),[files,setFiles]=useState<File[]>([]),[busy,setBusy]=useState(false),[message,setMessage]=useState(''),[blockers,setBlockers]=useState<string[]>([]);
  async function clone(){
    setBusy(true);setMessage('');setBlockers([]);
    try{
      const body=new FormData();files.forEach(file=>body.append('files',file));
      const response=await fetch(apiUrl('/dbf/clone'),{method:'POST',body});
      if(!response.ok){const error=await response.json();throw new Error(typeof error.detail==='string'?error.detail:'DBF patikra nepraėjo.');}
      const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');
      link.href=url;link.download='SISTELA-EXPERIMENTAL-CLONE.zip';document.body.appendChild(link);link.click();link.remove();
      setTimeout(()=>URL.revokeObjectURL(url),1000);
      setMessage('Sugeneruotas istorinio archyvo klonas. Dabartinis projektas neeksportuotas. Išpakuokite ZIP ir bandymui pasirinkite tik šešis DBF failus.');
    }catch(e){setMessage((e as Error).message);}finally{setBusy(false);}
  }
  async function inspect(){try{const plan=await api<{blockers:string[]}>(`/projects/${projectId}/dbf/plan`);setBlockers(plan.blockers);setMessage('Projekto DBF eksportui liko šios patikrintos kliūtys:');}catch(e){setMessage((e as Error).message);}}
  return <section className="dbf-experiment"><button onClick={()=>{setOpen(!open);if(!open)void inspect();}}>DBF eksportas</button><small>Eksperimentinis</small>{open&&<div><h3>DBF eksportas · Eksperimentinis</h3>{message&&<p role="status">{message}</p>}<ul>{blockers.map((b,i)=><li key={i}>{b}</li>)}</ul><details><summary>Papildomas istorinio archyvo klonavimo bandymas</summary><p><strong>Naudokite tik bandomai SISTELA sąmatai.</strong></p><p>Šis veiksmas atkuria pasirinktą istorinį archyvą. Dabartinio projekto DBF eksportas blokuojamas, kol nepatikrintas importas, skaičiavimai ir identifikatoriai.</p><p>Klonas išlaiko originalius identifikatorius. Importuokite tik atskirame bandymo kontekste, kad nepakeistumėte esamų sąmatų.</p><label>Šeši originalaus archyvo DBF failai<input aria-label="Šeši originalaus archyvo DBF failai" type="file" accept=".dbf" multiple disabled={busy} onChange={e=>setFiles(Array.from(e.target.files||[]))}/></label><button disabled={busy||files.length!==6} onClick={()=>void clone()}>{busy?'Generuojama…':'Atsisiųsti bandomąjį kloną ZIP'}</button><button disabled={busy} onClick={()=>void inspect()}>Tikrinti projekto DBF kliūtis</button>{blockers.length>0&&<details><summary>Techninės kliūtys kūrėjui ({blockers.length})</summary><ul>{blockers.map((b,i)=><li key={i}>{b}</li>)}</ul></details>}</details></div>}</section>;
}
