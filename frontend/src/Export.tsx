import './catalog-export.css';
import { useEffect, useState } from 'react';
import { api, apiUrl, post } from './api';
import { DbfExport } from './DbfExport';

interface Hierarchy {code:string;name:string}
interface ExportRow {id:string;selected_code:string;code_type:string;output_description:string;target_quantity:string;target_unit:string;options:{mark?:string;ngr?:number;parameters?:number[]}}
interface Model {complex:Hierarchy;object:Hierarchy;estimate:Hierarchy;period:string;filename:string;parameter89:number|null;sections:{id:string;code:string;name:string;coefficients:Record<string,string>;rows:ExportRow[]}[]}
interface Report {errors:{context:string;message:string}[];warnings:string[];records:string[]}

export function Export({projectId}:{projectId:string}) {
  const [model,setModel]=useState<Model>(),[report,setReport]=useState<Report>(),[busy,setBusy]=useState(false),[message,setMessage]=useState('');
  useEffect(()=>{let cancelled=false;void api<Model>(`/projects/${projectId}/export/model`).then(m=>{if(!cancelled)setModel(m);}).catch(e=>setMessage(e.message));return()=>{cancelled=true;};},[projectId]);
  function update(value:Partial<Model>){setModel(m=>m?{...m,...value}:m);setReport(undefined);}
  function rowOption(id:string,value:Partial<ExportRow['options']>){if(model)update({sections:model.sections.map(s=>({...s,rows:s.rows.map(r=>r.id===id?{...r,options:{...r.options,...value}}:r)}))});}
  async function save(){
    if(!model)return;
    const {complex,object,estimate,period,filename}=model;
    await api('/settings/sistela',{method:'PUT',body:JSON.stringify({parameter89:model.parameter89})});
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
  return <section className="info-panel export-panel"><h2>Eksportuoti į SISTELA</h2><p>TXT ir DBF perdavimas eksperimentinis. Entry Mode lieka prieinamas.</p>
    <details><summary>TXT eksportas · Informacija pakete</summary>{model&&<>
      <p>Nurodykite testui skirtus hierarchijos kodus ir tikrą SISTELA parametro reikšmę.</p>
      {(['complex','object','estimate'] as const).map((key,i)=><fieldset key={key}><legend>{['Kompleksas','Objektas','Lokalinė sąmata'][i]}</legend>
        <label>Kodas<input aria-label={`${key} kodas`} value={model[key].code} onChange={e=>update({[key]:{...model[key],code:e.target.value}})}/></label>
        <label>Pavadinimas<input aria-label={`${key} pavadinimas`} value={model[key].name} onChange={e=>update({[key]:{...model[key],name:e.target.value}})}/></label></fieldset>)}
      <label>Laikotarpis YYYYMM<input aria-label="Paketo laikotarpis" value={model.period} onChange={e=>update({period:e.target.value})}/></label>
      <label>Failo vardas (iki 8 raidžių / skaičių)<input aria-label="Paketo failo vardas" value={model.filename} onChange={e=>update({filename:e.target.value})}/></label>
      <label>SISTELA → Paketo kiekių perskaičiavimas<select aria-label="Parametras 89" value={model.parameter89??''} onChange={e=>update({parameter89:e.target.value===''?null:Number(e.target.value)})}><option value="">Nežinomas</option><option value="0">Parametras 89 = 0</option><option value="1">Parametras 89 = 1</option></select></label>
      <p>Assistant eksportuoja tikslinius kiekius. Patvirtinta konversija arba 100M vienetas su 89=1 blokuojamas, kad kiekis nebūtų perskaičiuotas du kartus.</p>
      {model.sections.map((s,index)=><fieldset key={s.id}><legend>Skyrius</legend><input aria-label={`Skyriaus kodas ${index+1}`} value={s.code} onChange={e=>update({sections:model.sections.map(x=>x.id===s.id?{...x,code:e.target.value}:x)})}/><input aria-label={`Skyriaus pavadinimas ${index+1}`} value={s.name} onChange={e=>update({sections:model.sections.map(x=>x.id===s.id?{...x,name:e.target.value}:x)})}/>
        {s.rows.map(r=><div key={r.id}><strong>{r.selected_code||'Trūksta kodo'}</strong> · {r.output_description} · {r.target_quantity} {r.target_unit} <small>{r.code_type==='custom'?'Vartotojo kodas':'Normatyvų katalogas'}</small>
          {r.code_type==='custom'&&<><label>Žymė<select aria-label={`Žymė ${r.id}`} value={r.options.mark||'S'} onChange={e=>rowOption(r.id,{mark:e.target.value})}><option value="S">S · Bendrastatybiniai darbai</option><option value="G">G · Grįžtamos medžiagos</option><option value="I">I · Įrenginiai</option></select></label>{r.options.mark!=='I'&&<label>NGR grupė<select aria-label={`NGR ${r.id}`} value={r.options.ngr||''} onChange={e=>rowOption(r.id,{ngr:Number(e.target.value)})}><option value="">Pasirinkite</option>{['Metalas','Vamzdžiai','Bendrastatybinės','Apdailos','Elektrotechninės','Santechninės','Langai / durys','Mediena','Izoliacija','Betonas','Pusfabrikačiai','Kitos'].map((n,i)=><option value={i+1} key={n}>{i+1} · {n}</option>)}</select></label>}<small>Kaina įvedama darbo lentelėje.</small></>}
          {r.code_type==='normative'&&r.selected_code.includes('P')&&<label>Parametrinio įkainio G (x arba x,y)<input aria-label={`G ${r.id}`} value={r.options.parameters?.join(',')||''} onChange={e=>rowOption(r.id,{parameters:e.target.value.split(',').map(Number)})}/></label>}
        </div>)}
      </fieldset>)}
      <button disabled={busy} onClick={()=>void run()}>Išsaugoti ir tikrinti TXT</button><button disabled={busy} onClick={()=>void run(true)}>Atsisiųsti TXT</button>
      {report&&<><ul>{report.errors.map((e,i)=><li key={i}>{e.context}: {e.message}</li>)}</ul>{report.warnings.map(w=><p key={w}>{w}</p>)}{!report.errors.length&&<><p>TXT paruoštas · EXPERIMENTAL</p><pre>{report.records.join('\n')}</pre><button onClick={()=>void navigator.clipboard.writeText(report.records.join('\r\n')+'\r\n').then(()=>setMessage('Paketo tekstas nukopijuotas.')).catch(e=>setMessage(e.message))}>Kopijuoti paketo tekstą</button></>}</>}
      <p>SISTELA kelias: Informacijos įvedimas → Informacija pakete → Tikrinti informaciją → Formuoti sąmatinę informaciją</p>
    </>}</details>
    <DbfExport projectId={projectId}/><button onClick={()=>void post('/exports/open-folder').catch(e=>setMessage(e.message))}>Atidaryti eksporto aplanką</button>{message&&<p role="status">{message}</p>}
  </section>;
}
