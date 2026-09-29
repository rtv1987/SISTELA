import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { HistoryScreen, type HistoricalLine } from './History';
import { MappingPanel } from './MappingPanel';
import { blankLine, type Line } from './types';

const mocks=vi.hoisted(()=>({api:vi.fn(),post:vi.fn()}));
vi.mock('./api',()=>({api:mocks.api,post:mocks.post}));
const candidate:HistoricalLine={id:'historical',version:1,description:'Detektorių montavimas',sistela_code:'TEST-270',unit:'vnt.',quantity:'28',historical_price:'10',system_type:'GSS',status:'CANDIDATE',evidence_type:'DERIVED',bulk_eligible:true,estimate_name:'Gaisro aptikimo sistema',project_name:'Demonstracinis objektas',section_name:'Darbai',line_type:'Work',system_evidence:'INFERENCE',source_date:null};
beforeEach(()=>{vi.clearAllMocks();mocks.post.mockResolvedValue({updated:1});mocks.api.mockImplementation(async(url:string)=>{
  if(url==='/history/imports')return [];
  if(url.endsWith('/evidence'))return {...candidate,imported_at:'2026-09-29',evidence:{header:{file:'dd-demo.dbf',record:42}},reviews:[]};
  return {total:1,items:[candidate]};
});});
afterEach(cleanup);

it('renders archive import, provenance and filters',async()=>{
  render(<HistoryScreen/>);
  expect(screen.getByLabelText('DBF archyvo failai')).toHaveAttribute('multiple');
  await screen.findByText('Detektorių montavimas');
  fireEvent.change(screen.getByLabelText('Istorijos sistema'),{target:{value:'GSS'}});
  fireEvent.change(screen.getByLabelText('Ieškoti istorijoje'),{target:{value:'detektorių'}});
  fireEvent.change(screen.getByLabelText('Istorijos SISTELA kodas'),{target:{value:'270'}});
  await waitFor(()=>expect(mocks.api.mock.calls.some(([url])=>String(url).includes('system=GSS')&&String(url).includes('code=270')&&String(url).includes('search=detektori'))).toBe(true));
  fireEvent.click(screen.getByRole('button',{name:'Įrodymai TEST-270'}));
  const drawer=await screen.findByRole('dialog',{name:'Istorinio pasiūlymo įrodymai'});
  await within(drawer).findByText('dd-demo.dbf · įrašas 42');
  expect(within(drawer).getByText('Demonstracinis objektas')).toBeInTheDocument();
  fireEvent.click(within(drawer).getByLabelText('Uždaryti įrodymus'));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
});

it('confirms a reviewed system and removes the row from candidate filter',async()=>{
  render(<HistoryScreen/>);await screen.findByText('Detektorių montavimas');
  fireEvent.click(screen.getByRole('button',{name:'Peržiūrėti'}));
  fireEvent.change(screen.getByLabelText('Patvirtinama istorijos sistema'),{target:{value:'AS'}});
  // Preserve the independent imports endpoint in the reload.
  mocks.post.mockImplementation(async()=>{mocks.api.mockImplementation(async(url:string)=>url==='/history/imports'?[]:{total:0,items:[]});return {updated:1};});
  fireEvent.click(screen.getByRole('button',{name:'Patvirtinti kandidatą'}));
  await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/history/review',expect.objectContaining({status:'CONFIRMED',items:[{id:'historical',version:1,system_type:'AS'}]})));
  await waitFor(()=>expect(screen.queryByText('Detektorių montavimas')).not.toBeInTheDocument());
});

it('rejects a candidate and refreshes normal candidate flow',async()=>{
  render(<HistoryScreen/>);await screen.findByText('Detektorių montavimas');
  mocks.post.mockImplementation(async()=>{mocks.api.mockImplementation(async(url:string)=>url==='/history/imports'?[]:{total:0,items:[]});return {updated:1};});
  fireEvent.click(screen.getByRole('button',{name:'Atmesti'}));
  await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/history/review',expect.objectContaining({status:'REJECTED'})));
  await waitFor(()=>expect(screen.queryByText('Detektorių montavimas')).not.toBeInTheDocument());
});

it('ambiguous evidence disables bulk selection and requires explicit acknowledgement',async()=>{
  mocks.api.mockImplementation(async(url:string)=>url==='/history/imports'?[]:{total:1,items:[{...candidate,evidence_type:'AMBIGUOUS',bulk_eligible:false}]});
  render(<HistoryScreen/>);await screen.findByText('Detektorių montavimas');
  expect(screen.getByRole('checkbox')).toBeDisabled();
  fireEvent.click(screen.getByRole('button',{name:'Peržiūrėti'}));
  expect(screen.getByRole('button',{name:'Patvirtinti kandidatą'})).toBeDisabled();
  fireEvent.click(screen.getByLabelText(/Peržiūrėjau neaiškią jungtį/));
  expect(screen.getByRole('button',{name:'Patvirtinti kandidatą'})).toBeEnabled();
});

it('historical suggestion opens evidence and convertible units block applying',async()=>{
  const line={...blankLine('GSS'),id:'current',project_id:'p',line_type:'Work',mapping_status:'unmapped',version:1,unit:'m'} as Line;
  mocks.api.mockImplementation(async(url:string)=>url.endsWith('/suggestions')?[{mapping_id:'history:historical',sistela_code:'TEST-270',sistela_description:'',source_unit:'100m',confidence:'.49',method:'exact',confirmed_count:0,compatible:false,origin:'historical',usage_count:14,project_count:6,estimate_count:6,evidence_ids:['historical'],evidence_quality:['DERIVED'],unit_compatibility:{status:'CONVERTIBLE',source:'m',target:'100m',factor:'.01'}}]:{...candidate,imported_at:'2026-09-29',evidence:{header:{file:'dd-demo.dbf',record:42}},reviews:[]});
  render(<MappingPanel line={line} busy={false} onApply={vi.fn()} onConfirm={vi.fn()}/>);
  await screen.findByText(/14 panaudojimai/);
  expect(screen.getByRole('button',{name:'Pritaikyti pasiūlymą'})).toBeDisabled();
  fireEvent.click(screen.getByText(/Istoriniai įrodymai/));
  fireEvent.click(screen.getByRole('button',{name:'Atverti šaltinį 1'}));
  await screen.findByRole('dialog',{name:'Istorinio pasiūlymo įrodymai'});
});
