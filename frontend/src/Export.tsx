import './catalog-export.css';
import { useEffect, useState } from 'react';
import { api, apiUrl, post } from './api';
import { DbfExport } from './DbfExport';

interface Hierarchy {code:string;name:string}
interface ExportRow {id:string;selected_code:string;code_type:string;output_description:string;target_quantity:string;target_unit:string;options:{mark?:string;ngr?:number;parameters?:number[]}}
interface Model {complex:Hierarchy;object:Hierarchy;estimate:Hierarchy;period:string;filename:string;parameter89:number|null;sections:{id:string;code:string;name:string;coefficients:Record<string,string>;rows:ExportRow[]}[]}
interface Report {errors:{context:string;message:string}[];warnings:string[];records:string[]}

export function Export({projectId,onSettings,onGrid}:{projectId:string;onSettings?:()=>void;onGrid?:(id:string)=>void}) {
  const [model,setModel]=useState<Model>(),[report,setReport]=useState<Report>(),[busy,setBusy]=useState(false),[message,setMessage]=useState('');
  useEffect(()=>{let cancelled=false;void api<Model>(`/projects/${projectId}/export/model`).then(m=>{if(!cancelled)setModel(m);}).catch(e=>setMessage(e.message));void api<Report>(`/projects/${projectId}/export/txt/validation`).then(r=>{if(!cancelled)setReport(r);}).catch(e=>setMessage(e.message));return()=>{cancelled=true;};},[projectId]);
  function update(value:Partial<Model>){setModel(m=>m?{...m,...value}:m);setReport(undefined);}
  async function save(){
    if(!model)return;
    const {complex,object,estimate,period,filename}=model;

    await api(`/projects/${projectId}/export/profile`,{method:'PUT',body:JSON.stringify({complex,object,estimate,period,filename,
      sections:Object.fromEntries(model.sections.map(s=>[s.id,{code:s.code,name:s.name,coefficients:s.coefficients}])),
      rows:Object.fromEntries(model.sections.flatMap(s=>s.rows.map(r=>[r.id,r.options])))})});
    const result=await api<Report>(`/projects/${projectId}/export/txt/validation`);setReport(result);return result;
  }
  async function run(download=false){setBusy(true);setMessage('');try{const result=await save();if(download&&result&&!result.errors.length){
    const response=await fetch(apiUrl(`/projects/${projectId}/export/txt`),{method:'POST'});
    if(!response.ok)throw new Error('Eksportas neparuoštas. Patikrinkite laukus dar kartą.');
    const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=model!.filename+'.TXT';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
    setMessage('TXT eksportas paruoštas · EXPERIMENTAL. Kopija išsaugota eksporto aplanke.');
  }}catch(e){setMessage((e as Error).message);}finally{setBusy(false);}}
  const total=model?.sections.reduce((n,s)=>n+s.rows.length,0)||0;
  const blocked=new Set(report?.errors.map(e=>e.context));
  const readyCount=model?.sections.flatMap(s=>s.rows).filter(r=>!blocked.has(r.id)).length||0;
  return <section className="info-panel export-panel"><h2>Eksportuoti į SISTELA</h2>
    <p role="status">{report ? report.errors.length ? `Reikia sutvarkyti ${report.errors.length} laukus` : 'Paruošta SISTELA' : 'Ruošiama…'}</p>
    <p>{readyCount} iš {total} eilučių paruošta</p>
    <div className="workflow-actions"><button className="primary" disabled={busy||!report||report.errors.length>0} onClick={()=>void run(true)}>TXT eksportas</button><span>Informacija pakete · Eksperimentinis</span></div>
    <DbfExport projectId={projectId}/>
    {report?.errors.length ? <div className="export-exceptions"><h3>Reikia sutvarkyti</h3><ul>{report.errors.map((e,i)=>{
      const row=model?.sections.flatMap(s=>s.rows).find(r=>r.id===e.context);
      return <li key={i}>{row?.output_description}: {e.message} {row&&onGrid&&<button onClick={()=>onGrid(row.id)}>Redaguoti lentelėje</button>}{e.context==='parameter89'&&onSettings&&<button onClick={onSettings}>Atverti SISTELA nustatymus</button>}</li>;
    })}</ul></div>:null}
    <details><summary>Eksporto nustatymai</summary>{model&&<>
      {(['complex','object','estimate'] as const).map((key,i)=><fieldset key={key}><legend>{['Kompleksas','Objektas','Lokalinė sąmata'][i]}</legend>
        <label>Kodas<input aria-label={`${key} kodas`} value={model[key].code} onChange={e=>update({[key]:{...model[key],code:e.target.value}})}/></label>
        <label>Pavadinimas<input aria-label={`${key} pavadinimas`} value={model[key].name} onChange={e=>update({[key]:{...model[key],name:e.target.value}})}/></label></fieldset>)}
      <label>Laikotarpis YYYYMM<input aria-label="Paketo laikotarpis" value={model.period} onChange={e=>update({period:e.target.value})}/></label>
      <label>Failo vardas<input aria-label="Paketo failo vardas" value={model.filename} onChange={e=>update({filename:e.target.value})}/></label>
      {model.sections.map((s,index)=><fieldset key={s.id}><legend>Skyrius</legend><input aria-label={`Skyriaus kodas ${index+1}`} value={s.code} onChange={e=>update({sections:model.sections.map(x=>x.id===s.id?{...x,code:e.target.value}:x)})}/><input aria-label={`Skyriaus pavadinimas ${index+1}`} value={s.name} onChange={e=>update({sections:model.sections.map(x=>x.id===s.id?{...x,name:e.target.value}:x)})}/></fieldset>)}
      <button disabled={busy} onClick={()=>void run()}>Išsaugoti eksporto nustatymus</button>
    </>}</details>
    <details><summary>Techninės detalės / TXT peržiūra</summary>{report?.warnings.map(w=><p key={w}>{w}</p>)}{report&&!report.errors.length&&<><pre>{report.records.join('\n')}</pre><button onClick={()=>void navigator.clipboard.writeText(report.records.join('\r\n')+'\r\n').then(()=>setMessage('Visas paketo tekstas nukopijuotas.')).catch(e=>setMessage(e.message))}>Kopijuoti paketo tekstą</button></>}</details>
    <p>SISTELA: Informacijos įvedimas → Informacija pakete → Tikrinti informaciją → Formuoti sąmatinę informaciją. Perduodama visa sąmata vienu paketu.</p>
    <button onClick={()=>void post('/exports/open-folder').catch(e=>setMessage(e.message))}>Atidaryti eksporto aplanką</button>{message&&<p role="status">{message}</p>}
  </section>;
}
