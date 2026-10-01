import { useEffect, useState } from 'react';
import { api } from './api';

export function SistelaSettings(){
  const [value,setValue]=useState(''),[message,setMessage]=useState(''),[busy,setBusy]=useState(false);
  useEffect(()=>{void api<{parameter89:number|null}>('/settings/sistela').then(r=>setValue(r.parameter89===null?'':String(r.parameter89))).catch(e=>setMessage(e.message));},[]);
  async function save(next:string){setBusy(true);try{await api('/settings/sistela',{method:'PUT',body:JSON.stringify({parameter89:next===''?null:Number(next)})});setValue(next);setMessage('SISTELA nustatymas išsaugotas visiems projektams.');}catch(e){setMessage((e as Error).message);}finally{setBusy(false);}}
  return <section className="info-panel"><h2>Nustatymai → SISTELA</h2><label>Paketo kiekių perskaičiavimas<select aria-label="Parametras 89" value={value} disabled={busy} onChange={e=>void save(e.target.value)}><option value="">Nežinomas</option><option value="0">89 = 0</option><option value="1">89 = 1</option></select></label><p>Pasirinkite tikrą reikšmę iš SISTELA nustatymų. Ji galioja visiems projektams. Konvertuotiems arba 100M kiekiams reikia 89 = 0, kad kiekis nebūtų perskaičiuotas antrą kartą.</p>{message&&<p role="status">{message}</p>}</section>;
}
