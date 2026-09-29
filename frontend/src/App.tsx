import { useCallback, useEffect, useRef, useState } from 'react';
import * as Tabs from '@radix-ui/react-tabs';
import { Plus, Upload, Copy, Trash2, Undo2, FolderOpen, Check, ShieldCheck, ChevronRight, FileText, X, ArrowRight, Download } from 'lucide-react';
import type { RowSelectionState } from '@tanstack/react-table';
import { api, post, apiUrl } from './api';
import { EstimateGrid } from './Grid';
import { MappingPanel } from './MappingPanel';
import { Workflow } from './Workflow';
import { EntryMode } from './EntryMode';
import { ExcelPanel, pasteLines } from './ExcelPanel';
import { HistoryScreen } from './History';
import './history.css';
import { blankLine, type Line, type Project, type ImportRun, type Capability } from './types';

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectId] = useState('');
  const [historyView, setHistoryView] = useState(false);
  const [lines, setLines] = useState<Line[]>([]); const latest = useRef<Line[]>([]);
  const [imports, setImports] = useState<ImportRun[]>([]);
  const [selection, setSelection] = useState<RowSelectionState>({}); const [active, setActive] = useState('');
  const [pending, setPending] = useState(0); const [error, setError] = useState(''); const [undo, setUndo] = useState(false);
  const [newProject, setNewProject] = useState(false); const [name, setName] = useState(''); const [system, setSystem] = useState('GSS');
  const [panel, setPanel] = useState(''); const [capabilities, setCapabilities] = useState<Capability[]>([]);
  const [bulkField, setBulkField] = useState('notes'); const [bulkValue, setBulkValue] = useState('');
  const [mode, setMode] = useState('grid'); const queue = useRef(Promise.resolve());
  const upload = useRef<HTMLInputElement>(null);
  const current = projects.find(p => p.id === projectId);
  const selected = Object.keys(selection).filter(id => selection[id]);
  const activeLine = lines.find(l => l.id === active);
  const replaceLines = useCallback((value: Line[]) => { latest.current = value; setLines(value); }, []);
  const reloadProjects = useCallback(async () => { const value = await api<Project[]>('/projects'); setProjects(value); return value; }, []);
  useEffect(() => { void reloadProjects().then(value => setProjectId(value[0]?.id || '')).catch(e => setError(e.message)); void api<Capability[]>('/integration/capabilities').then(setCapabilities).catch(e => setError(e.message)); }, [reloadProjects]);
  useEffect(() => {
    let cancelled = false; setSelection({}); setActive(''); setUndo(false); replaceLines([]); setImports([]);
    if (projectId) void Promise.all([api<Line[]>(`/projects/${projectId}/lines`), api<ImportRun[]>(`/projects/${projectId}/imports`)]).then(([value, runs]) => { if (!cancelled) { replaceLines(value); setActive(value.find(l => l.line_type === 'Work')?.id || value[0]?.id || ''); setImports(runs); } }).catch(e => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [projectId, replaceLines]);
  const enqueue = useCallback((job: (rows: Line[]) => Promise<Line[] | void>, allowUndo = true): Promise<void> => {
    setPending(n => n + 1); setError('');
    const task = queue.current.then(async () => { const result = await job(latest.current); if (result) replaceLines(result); setUndo(allowUndo); });
    queue.current = task.catch(() => {});
    return task.catch(e => { setError(e.message || 'Operacija nepavyko.'); throw e; }).finally(() => setPending(n => n - 1));
  }, [replaceLines]);
  const onEdit = useCallback((id: string, field: string, value: string | null) => enqueue(rows => {
    const line = rows.find(l => l.id === id); if (!line) throw new Error('Eilutė nerasta.');
    return post<Line[]>(`/projects/${projectId}/grid`, { edits: [{ id, version: line.version, values: { [field]: value } }] });
  }), [enqueue, projectId]);
  const act = (job: (rows: Line[]) => Promise<Line[] | void>, canUndo = true) => { void enqueue(job, canUndo).catch(() => {}); };
  const createProject = async () => { try { const result = await post<Project>('/projects', { name, system_type: system }); await reloadProjects(); setProjectId(result.id); setNewProject(false); setName(''); } catch (e) { setError((e as Error).message); } };
  const importPdf = (file: File) => act(async () => {
    const form = new FormData(); form.set('file', file);
    const run = await api<ImportRun>(`/projects/${projectId}/imports/pdf`, { method: 'POST', body: form });
    setImports(await api<ImportRun[]>(`/projects/${projectId}/imports`)); setPanel('imports');
    if (run.status === 'failed') throw new Error(run.error_message || 'Importas nepavyko.');
    return api<Line[]>(`/projects/${projectId}/lines`);
  }, false);
  return <div className={`app-shell ${mode === 'entry' ? 'entry-active' : ''}`}>
    <aside className="sidebar"><div className="brand"><span className="brand-mark">S</span><div>SISTELA<span>ASSISTANT</span></div></div>
      <div className="sidebar-label">DARBO VIETA</div><button className={`nav-item ${!historyView ? 'selected' : ''}`} onClick={() => {setHistoryView(false);setPanel('');}}><FolderOpen size={17}/> Projektai <span>{projects.length}</span></button>
      <button className={`nav-item ${historyView ? 'selected' : ''}`} onClick={() => {setHistoryView(true);setPanel('');}}>Istorinės SISTELA sąmatos</button><div className="sidebar-heading"><span>MANO PROJEKTAI</span><button aria-label="Naujas projektas" title="Naujas projektas" onClick={() => setNewProject(!newProject)}><Plus size={16}/></button></div>
      {newProject && <form className="project-form" onSubmit={e => { e.preventDefault(); void createProject(); }}><input autoFocus aria-label="Projekto pavadinimas" placeholder="Projekto pavadinimas" value={name} onChange={e => setName(e.target.value)} required/><select aria-label="Naujo projekto sistema" value={system} onChange={e => setSystem(e.target.value)}>{['GSS','AS','VS','IK','ER','LER'].map(s => <option key={s}>{s}</option>)}</select><button className="primary" type="submit">Sukurti projektą</button></form>}
      <div className="project-list">{projects.map(p => <button key={p.id} disabled={pending > 0} className={`project-item ${p.id === projectId ? 'current' : ''}`} onClick={() => {setHistoryView(false);setProjectId(p.id);}}><FileText size={17}/><span>{p.name}<small>{p.system_type} · vietinis projektas</small></span></button>)}</div>
      <div className="sidebar-bottom"><button onClick={() => setPanel(panel === 'capabilities' ? '' : 'capabilities')}><ShieldCheck size={16}/> Integracijos</button><div className="local-badge"><span/> Viskas šiame kompiuteryje</div></div>
    </aside>
    <main className="workspace"><header className="topbar"><div className="breadcrumb">Projektai <ChevronRight size={13}/> {historyView ? 'Istorinės sąmatos' : current?.system_type || 'Naujas projektas'}</div><div className="save-state">{pending ? <><span className="spinner"/> Išsaugoma…</> : error ? 'Pakeitimas neišsaugotas' : <><Check size={14}/> Išsaugota lokaliai</>}</div></header>
      {error && <div role="alert" className="error-banner">{error}<button aria-label="Uždaryti klaidą" onClick={() => setError('')}><X size={15}/></button></div>}
      {historyView ? <HistoryScreen/> : !current ? <section className="welcome"><div className="welcome-icon"><FileText size={36}/></div><p className="eyebrow">NUO PROJEKTO IKI SĄMATOS</p><h1>Mažiau suvedimo.<br/>Daugiau tikslumo.</h1><p>Sukurkite projektą, importuokite žiniaraštį ir paruoškite eilutes darbui su SISTELA.</p><button className="primary" onClick={() => setNewProject(true)}><Plus size={17}/> Naujas projektas</button></section> : <>
      <section className="project-title"><div><p className="eyebrow">SĄNAUDŲ KIEKIŲ ŽINIARAŠTIS</p><h1>{current.name}</h1><div className="project-meta"><span className="system-chip">{current.system_type}</span><span>{lines.filter(l => l.line_type === 'Material').length} medžiagų</span><span>{lines.filter(l => l.line_type === 'Work').length} darbų</span><span className="review-count">{lines.filter(l => l.line_type === 'Work' && l.mapping_status !== 'confirmed').length} darbų reikia patikrinti</span></div></div><button className="quiet" disabled={pending > 0} onClick={() => { void post<Project>(`/projects/${projectId}/duplicate`).then(async p => { await reloadProjects(); setProjectId(p.id); }).catch(e => setError(e.message)); }}><Copy size={15}/> Dubliuoti projektą</button></section>
      <Tabs.Root value={mode} onValueChange={setMode}><div className="modebar"><Tabs.List aria-label="Darbo režimas"><Tabs.Trigger value="grid">Darbo lentelė</Tabs.Trigger><Tabs.Trigger value="review">Peržiūra</Tabs.Trigger><Tabs.Trigger value="ready">Paruošta SISTELA</Tabs.Trigger><Tabs.Trigger value="entry">SISTELA Entry Mode <ArrowRight size={14}/></Tabs.Trigger></Tabs.List><button onClick={() => setPanel(panel === 'imports' ? '' : 'imports')}>Importo informacija <span className="count">{imports.length}</span></button></div>
      <Tabs.Content value="grid"><div className="toolbar"><button className="primary" disabled={!!pending} onClick={() => upload.current?.click()}><Upload size={15}/> Importuoti PDF</button><input ref={upload} type="file" hidden accept=".pdf" aria-label="PDF failas" onChange={e => { if (e.target.files?.[0]) importPdf(e.target.files[0]); e.target.value = ''; }}/><button disabled={!!pending} onClick={() => act(() => post(`/projects/${projectId}/grid`, { creates: [blankLine(current.system_type)] }))}><Plus size={15}/> Pridėti eilutę</button><span className="toolbar-divider"/><button title="Dubliuoti pažymėtas eilutes" disabled={!selected.length || !!pending} onClick={() => act(rows => post(`/projects/${projectId}/grid`, { duplicates: rows.filter(l => selected.includes(l.id)).map(l => ({ id: l.id, version: l.version })) }))}><Copy size={15}/></button><button title="Ištrinti pažymėtas eilutes" disabled={!selected.length || !!pending} onClick={() => { act(rows => post(`/projects/${projectId}/grid`, { deletes: rows.filter(l => selected.includes(l.id)).map(l => ({ id: l.id, version: l.version })) })); setSelection({}); }}><Trash2 size={15}/></button><button title="Atšaukti paskutinį lentelės veiksmą" disabled={!undo || !!pending} onClick={() => act(() => post(`/projects/${projectId}/undo`), false)}><Undo2 size={15}/></button><span className="toolbar-space"/><button onClick={() => setPanel(panel === 'excel' ? '' : 'excel')}><FileText size={15}/> Excel importas</button><a className="button" href={apiUrl(`/projects/${projectId}/export.xlsx`)}><Download size={15}/> XLSX</a></div>
        {selected.length > 0 && <div className="bulkbar"><strong>{selected.length} pažymėta</strong><select aria-label="Masinio keitimo laukas" value={bulkField} onChange={e => setBulkField(e.target.value)}><option value="notes">Pastabos</option><option value="system_type">Sistema</option><option value="line_type">Tipas (Material / Work / Other)</option><option value="unit">Vienetas</option><option value="material_price">Medžiagos kaina</option><option value="work_price">Darbo kaina</option></select><input aria-label="Masinio keitimo reikšmė" value={bulkValue} placeholder="Nauja reikšmė" onChange={e => setBulkValue(e.target.value)}/><button disabled={!!pending} onClick={() => act(rows => post(`/projects/${projectId}/grid`, { edits: rows.filter(l => selected.includes(l.id)).map(l => ({ id: l.id, version: l.version, values: { [bulkField]: bulkValue } })) }))}>Taikyti</button><button onClick={() => setSelection({})}>Atžymėti</button></div>}
        <div className="editing-layout" onPaste={e => {
  const text = e.clipboardData.getData('text/plain');
  if (!text.includes('\t')) return;
  e.preventDefault();
  try { const creates = pasteLines(text, current.system_type); act(() => post(`/projects/${projectId}/grid`, { creates })); }
  catch (err) { setError((err as Error).message); }
}}><EstimateGrid lines={lines} active={active} onActive={setActive} onEdit={onEdit} selection={selection} setSelection={setSelection}/>{activeLine && <aside className="detail-panel"><p className="eyebrow">PASIRINKTA EILUTĖ</p><h3>{activeLine.project_description}</h3><p className="muted">{activeLine.technical_reference || 'Modelis nenurodytas'} · {activeLine.quantity} {activeLine.unit}</p><MappingPanel line={activeLine} busy={!!pending} onApply={suggestion => enqueue(async rows => {
  const latestLine = rows.find(l => l.id === activeLine.id)!;
  const result = await post<Line>(`/projects/${projectId}/lines/${activeLine.id}/mapping/apply`, { version: latestLine.version, mapping_id: suggestion.mapping_id });
  return rows.map(l => l.id === result.id ? result : l);
}, false)} onConfirm={(code, original, unit) => enqueue(async rows => {
  const latestLine = rows.find(l => l.id === activeLine.id)!;
  const result = await post<Line>(`/projects/${projectId}/lines/${activeLine.id}/mapping/confirm`, { version: latestLine.version, sistela_code: code, sistela_original_description: original, normative_unit: unit });
  return rows.map(l => l.id === result.id ? result : l);
}, false)}/><div className="source-detail"><strong>Šaltinio atsekamumas</strong><p>{activeLine.source_page ? `PDF, ${activeLine.source_page} puslapis · pozicija ${activeLine.source_position}` : 'Rankinė / Excel eilutė'}</p><details><summary>Originalūs duomenys</summary><pre>{activeLine.source_raw_text || 'Šaltinio nėra'}</pre></details></div></aside>}</div>
      </Tabs.Content>{['review','ready'].map(value => <Tabs.Content key={value} value={value}><Workflow projectId={projectId} lines={lines} ready={value==='ready'} busy={!!pending} onChange={job=>enqueue(job,false)} onEntry={()=>setMode('entry')} onGrid={id=>{if(id==='review'){setMode('review');}else{setActive(id);setMode('grid');}}}/></Tabs.Content>)}<Tabs.Content value="entry"><EntryMode worksOnly onExit={()=>setMode('ready')} lines={lines} busy={!!pending} onReview={id => { setActive(id); setMode('grid'); }} onMark={(line, entered) => enqueue(async rows => {
  const latestLine = rows.find(l => l.id === line.id)!;
  const result = await post<Line>(`/projects/${projectId}/lines/${line.id}/entry`, { version: latestLine.version, entered });
  return rows.map(l => l.id === result.id ? result : l);
}, false)}/></Tabs.Content></Tabs.Root>
      </>}
      {panel === 'imports' && <section className="info-panel"><div className="panel-heading"><h3>Importo informacija</h3><button onClick={() => setPanel('')} aria-label="Uždaryti importo informaciją"><X size={17}/></button></div>{!imports.length && <p>Importų dar nėra.</p>}{imports.map(run => <div key={run.id} className="import-row"><strong>{run.status === 'failed' ? 'Nepavyko importuoti' : 'Importuota – reikia peržiūros'}</strong><span>{run.rows_detected} eilučių · puslapiai {run.pages.join(', ') || '—'}</span>{run.error_message && <p className="error-text">{run.error_message}</p>}{run.warnings.map((w, i) => <p key={i}>{w.page ? `${w.page} p.: ` : ''}{w.message}</p>)}</div>)}</section>}
      {panel === 'capabilities' && <section className="info-panel"><div className="panel-heading"><h3>Integracijos galimybės</h3><button onClick={() => setPanel('')}><X size={17}/></button></div>{capabilities.map(c => <div className="capability" key={c.id}><strong>{c.name}</strong><span className={`status ${c.status === 'available' ? 'confirmed' : ''}`}>{c.status === 'available' ? 'Veikia' : c.status === 'blocked' ? 'Nepatvirtinta' : 'Tik analizė'}</span><p>{c.limitation}</p></div>)}</section>}
      {panel === 'excel' && current && <ExcelPanel system={current.system_type} busy={!!pending} onClose={() => setPanel('')} onImport={form => enqueue(async () => {
  const run = await api<ImportRun>(`/projects/${projectId}/imports/xlsx`, { method:'POST', body:form });
  setImports(await api<ImportRun[]>(`/projects/${projectId}/imports`));
  if (run.status === 'failed') throw new Error(run.error_message || 'Importas nepavyko.');
  setPanel('imports'); return api<Line[]>(`/projects/${projectId}/lines`);
}, false)} onPaste={creates => enqueue(() => post(`/projects/${projectId}/grid`, { creates }))}/>}
    </main>
  </div>;
}
