import { useEffect, useState } from 'react';
import { api, post } from './api';
import type { Project } from './types';
import './lifecycle.css';

export function TrashConfirmation({project,onCancel,onConfirm,busy}:{project:Project;onCancel:()=>void;onConfirm:()=>void;busy:boolean}) {
  return <div className="modal-shade"><section role="dialog" aria-modal="true" aria-label="Perkelti projektą į šiukšlinę" className="lifecycle-dialog"><h2>Perkelti į šiukšlinę?</h2><p>{project.name}</p><p>Projektą galėsite atkurti. Bendra normatyvų ir DBF istorija lieka.</p><div><button disabled={busy} onClick={onCancel}>Atšaukti</button><button disabled={busy} className="primary" onClick={onConfirm}>Perkelti į šiukšlinę</button></div></section></div>;
}

export function TrashScreen({onChanged}:{onChanged:()=>Promise<unknown>}) {
  const [projects,setProjects]=useState<Project[]>([]), [removing,setRemoving]=useState<Project|null>(null);
  const [confirmation,setConfirmation]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[notice,setNotice]=useState('');
  useEffect(()=>{let cancelled=false;void api<Project[]>('/trash').then(p=>{if(!cancelled)setProjects(p);}).catch(e=>setError(e.message));return()=>{cancelled=true;};},[]);
  async function action(project:Project,remove:boolean) {
    setBusy(true);setError('');
    try {
      const result=await post<{retained_copy_count?:number}>(`/projects/${project.id}/${remove?'delete':'restore'}`,remove?{confirmation}:{});
      setProjects(await api<Project[]>('/trash'));await onChanged();setRemoving(null);setConfirmation('');
      setNotice(remove?`Projektas ištrintas. Bendra istorija išsaugota.${result.retained_copy_count?' Kai kurių užimtų kopijų pašalinti nepavyko.':''}`:'Projektas atkurtas.');
    } catch(e){setError((e as Error).message);}finally{setBusy(false);}
  }
  return <section className="trash-screen"><h1>Šiukšlinė</h1><p>Projektus galima atkurti. Galutinis ištrynimas nepanaikina bendros SISTELA patirties.</p>{error&&<p role="alert">{error}</p>}{notice&&<p role="status">{notice}</p>}{!projects.length&&<p>Šiukšlinė tuščia.</p>}{projects.map(project=><article key={project.id}><div><strong>{project.name}</strong><small>{project.system_type}</small></div><button disabled={busy} onClick={()=>void action(project,false)}>Atkurti</button><button disabled={busy} onClick={()=>{setRemoving(project);setConfirmation('');}}>Ištrinti visam laikui</button></article>)}
    {removing&&<div className="modal-shade"><section role="dialog" aria-modal="true" aria-label="Galutinis projekto ištrynimas" className="lifecycle-dialog"><h2>Ištrinti visam laikui?</h2><p>Eilutės, suvedimo eiga ir šio projekto dokumentų kopijos bus pašalintos. Originalūs failai ir bendra istorija lieka.</p><p>Patvirtinimui įveskite: <strong>{removing.name}</strong></p><input autoFocus aria-label="Trinamo projekto pavadinimas" value={confirmation} onChange={e=>setConfirmation(e.target.value)}/><div><button disabled={busy} onClick={()=>setRemoving(null)}>Atšaukti</button><button disabled={busy||confirmation!==removing.name} onClick={()=>void action(removing,true)}>Patvirtinti galutinį ištrynimą</button></div></section></div>}
  </section>;
}

export function ApplicationControls({busy,onStopped}:{busy:boolean;onStopped:()=>void}) {
  const [info,setInfo]=useState<{version:string;managed:boolean}>(),[error,setError]=useState('');
  useEffect(()=>{void api<{version:string;managed:boolean}>('/app/info').then(setInfo).catch(()=>{});},[]);
  async function act(path:string){try{await post(path);if(path.endsWith('/quit'))onStopped();}catch(e){setError((e as Error).message);}}
  return <div className="application-controls">{info&&<small>SISTELA Assistant {info.version}</small>}<button onClick={()=>void act('/app/logs/open')}>Atidaryti logų aplanką</button>{info?.managed&&<button disabled={busy} onClick={()=>void act('/app/quit')}>Uždaryti programą</button>}{error&&<p role="alert">{error}</p>}</div>;
}
