import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { Catalog } from './Catalog';
import { Export } from './Export';
import { SistelaSettings } from './SistelaSettings';
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
it('persists parameter 89 globally under settings',async()=>{
  mocks.api.mockResolvedValue({parameter89:null});render(<SistelaSettings/>);
  await screen.findByLabelText('Parametras 89');
  fireEvent.change(screen.getByLabelText('Parametras 89'),{target:{value:'0'}});
  await screen.findByText('SISTELA nustatymas išsaugotas visiems projektams.');
  expect(mocks.api).toHaveBeenCalledWith('/settings/sistela',{method:'PUT',body:'{"parameter89":0}'});
});
it('shows bulk export actions without per-row forms or readiness ceremony',async()=>{
  const model={complex:{code:'TEST',name:'Test'},object:{code:'1',name:'Test'},estimate:{code:'1',name:'Test'},period:'202609',filename:'TESTTXT',parameter89:0,sections:[{id:'s',code:'1',name:'Medžiagos',coefficients:{},rows:[{id:'r',selected_code:'A123',code_type:'custom',output_description:'Fixture',options:{mark:'S',ngr:12}}]}]};
  mocks.api.mockImplementation(async(url:string)=>url.endsWith('/model')?model:{errors:[],warnings:[],records:[]});
  render(<Export projectId="p"/>);
  await screen.findByText('1 iš 1 eilučių paruošta');
  expect(screen.getByRole('button',{name:'TXT eksportas'})).toBeEnabled();
  expect(screen.getByRole('button',{name:'DBF eksportas'})).toBeVisible();
  expect(screen.queryByLabelText('Parametras 89')).not.toBeInTheDocument();
  expect(screen.queryByText('NGR grupė')).not.toBeInTheDocument();
  expect(screen.queryByText('Patikrinti parengtį')).not.toBeInTheDocument();
});
it('links genuine missing prices to the work table',async()=>{
  mocks.api.mockImplementation(async(url:string)=>url.endsWith('/model')?{complex:{code:'T',name:'Test'},object:{code:'1',name:'Test'},estimate:{code:'1',name:'Test'},period:'202609',filename:'TEST',sections:[{id:'s',code:'1',name:'Material',rows:[{id:'r',output_description:'Fixture'}]}]}:{errors:[{context:'r',message:'Trūksta kainos'}],warnings:[],records:[]});
  const grid=vi.fn();render(<Export projectId="p" onGrid={grid}/>);
  fireEvent.click(await screen.findByRole('button',{name:'Redaguoti lentelėje'}));
  expect(grid).toHaveBeenCalledWith('r');
  expect(screen.getByRole('button',{name:'TXT eksportas'})).toBeDisabled();
});
it('a selected valid code is Entry Mode ready without CONFIRMED',()=>{
  expect(entryReady({...blankLine('GSS'),quantity:'1',unit:'m',line_type:'Work',sistela_code:'TEST-1',mapping_status:'suggested'} as Line)).toBe(true);
});

it('explains catalog versus custom prices and automatic text preparation',async()=>{
  const model={complex:{code:'T',name:'Test'},object:{code:'1',name:'Test'},estimate:{code:'1',name:'Test'},period:'202610',filename:'TEST',sections:[]};
  mocks.api.mockImplementation(async(url:string)=>url.endsWith('/model')?model:{errors:[],warnings:[],records:[],price_cases:[{id:'a',description:'Catalog material',category:'B',reason:'No explicit package price required',explicit_price_required:false},{id:'b',description:'Custom material',category:'C',reason:'Documented price required',explicit_price_required:true}],text_preparations:[{id:'b',original:'Pipe, fittings',text:'Pipe; fittings',rules:['list_comma_to_semicolon']}]});
  render(<Export projectId="p"/>);
  expect(await screen.findByText(/TXT skyryba sutvarkyta automatiškai: 1/)).toBeVisible();
  fireEvent.click(screen.getByText('Kainų pagrindimas'));
  expect(screen.getByText(/Kainą parenka SISTELA/)).toBeVisible();
  expect(screen.getByText(/Vartotojo pozicija/)).toBeVisible();
});
