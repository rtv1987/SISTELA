import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Catalog } from './Catalog';
import { Export } from './Export';
import { entryReady } from './EntryMode';
import { blankLine, type Line } from './types';
const mocks=vi.hoisted(()=>({api:vi.fn(),post:vi.fn()}));
vi.mock('./api',()=>({api:mocks.api,post:mocks.post,apiUrl:(url:string)=>url}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
it('searches local catalog and uses an entry without additional confirmation',async()=>{
  const entry={id:'rate',code:'TEST-1',description:'Kabelio montavimas',unit:'m',unit_id:'1',category:'TEST',kind:'rate',filename:'erer.dbf',record_number:1};
  mocks.api.mockImplementation(async(url:string)=>url.includes('/search')?[entry]:[]);
  const use=vi.fn().mockResolvedValue(undefined);render(<Catalog onUse={use}/>);
  fireEvent.change(screen.getByLabelText('Ieškoti normatyvų'),{target:{value:'TEST-1'}});
  await screen.findByText('Kabelio montavimas');
  fireEvent.click(screen.getByRole('button',{name:'Naudoti projekte'}));
  await waitFor(()=>expect(use).toHaveBeenCalledWith(entry));
});
it('imports a local folder and refreshes the catalog',async()=>{
  mocks.api.mockResolvedValue([]);mocks.post.mockResolvedValue({});render(<Catalog/>);
  fireEvent.change(screen.getByLabelText('Normatyvų aplankas'),{target:{value:'C:\\licensed'}});
  fireEvent.click(screen.getByRole('button',{name:'Importuoti / Atnaujinti katalogą'}));
  await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/normative/folder',{path:'C:\\licensed'}));
  await waitFor(()=>expect(mocks.api.mock.calls.filter(([url])=>url==='/normative/sources').length).toBe(2));
});
it('persists an explicit parameter 89 before TXT validation',async()=>{
  const model={complex:{code:'TEST',name:'Test'},object:{code:'1',name:'Test'},estimate:{code:'1',name:'Test'},period:'202609',filename:'TESTTXT',parameter89:null,sections:[]};
  mocks.api.mockImplementation(async(url:string)=>url.endsWith('/model')?model:url.endsWith('/validation')?{errors:[{context:'project',message:'Sąmatoje nėra eilučių.'}],warnings:[],records:[]}:{});
  render(<Export projectId="p"/>);fireEvent.click(screen.getByText('TXT eksportas · Informacija pakete'));
  await screen.findByLabelText('Parametras 89');expect(screen.getByLabelText('Parametras 89')).toHaveValue('');
  fireEvent.change(screen.getByLabelText('Parametras 89'),{target:{value:'0'}});
  fireEvent.click(screen.getByRole('button',{name:'Išsaugoti ir tikrinti TXT'}));
  await screen.findByText('project: Sąmatoje nėra eilučių.');
  expect(mocks.api).toHaveBeenCalledWith('/settings/sistela',{method:'PUT',body:'{"parameter89":0}'});
  expect(screen.getByRole('button',{name:'DBF eksportas'})).toBeInTheDocument();
});
it('a selected valid code is Entry Mode ready without CONFIRMED',()=>{
  expect(entryReady({...blankLine('GSS'),quantity:'1',unit:'m',line_type:'Work',sistela_code:'TEST-1',mapping_status:'suggested'} as Line)).toBe(true);
});
