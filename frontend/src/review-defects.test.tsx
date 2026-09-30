import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { App } from './App';
import { MappingPanel } from './MappingPanel';
import { conversionFactor } from './conversion';
import { blankLine, type Line } from './types';

const mocks=vi.hoisted(()=>({api:vi.fn(),post:vi.fn()}));
vi.mock('./api',()=>({api:mocks.api,post:mocks.post,apiUrl:(url:string)=>url}));
const line={...blankLine('GSS'),id:'line',project_id:'project',line_type:'Work',project_description:'Detektorių montavimas',output_description:'Detektorių montavimas',unit:'vnt.',quantity:'28',version:1,confidence:null,source_position:'1',source_page:null,source_raw_text:'',sort_order:0,entered_at:null,mapping_status:'unmapped',review_data:{}} as Line;
const low={mapping_id:'low',sistela_code:'N50-314',confidence:'.46',source_unit:'vnt.',sistela_description:'',compatible:true,confirmed_count:0,origin:'historical'};
const confirmed={...low,mapping_id:'history:detector',sistela_code:'N50-270',confidence:'.28',confirmed_count:1,historical_confirmed:true,evidence_ids:['detector'],matching_descriptions:['Historical detector wording']};
beforeEach(()=>{vi.clearAllMocks();mocks.api.mockResolvedValue([]);});
afterEach(cleanup);

it.each([['vnt','vnt.',null],['kompl','kompl.',null],['m','m',null],['m','100M','0.01'],['100M','m','100'],['vnt','100M',null],['m','',null]])('conversion requires actual relevant target: %s → %s',(source,target,factor)=>{
  expect(conversionFactor(source,target)).toBe(factor);
});

it.each([['vnt.','vnt.'],['kompl.','kompl.'],['m','m'],['vnt.','100M'],['m','']])('hides conversion panel for %s → %s',async(source,target)=>{
  const {container}=render(<MappingPanel line={{...line,unit:source}} busy={false} onConvert={vi.fn()} onApply={vi.fn()} onConfirm={vi.fn()}/>);
  await waitFor(()=>expect(mocks.api).toHaveBeenCalled());
  fireEvent.change(screen.getByLabelText('Normatyvo vienetas'),{target:{value:target}});
  expect(container.querySelector('.conversion-review')).toBeNull();
  expect(screen.queryByLabelText('Tikslinis konversijos vienetas')).not.toBeInTheDocument();
});

it('shows conversion only after a real normative target is supplied and requires explicit acceptance',async()=>{
  const accept=vi.fn().mockResolvedValue(undefined);
  const {container}=render(<MappingPanel line={{...line,unit:'m',quantity:'650'}} busy={false} onConvert={accept} onApply={vi.fn()} onConfirm={vi.fn()}/>);
  await waitFor(()=>expect(mocks.api).toHaveBeenCalled());
  expect(container.querySelector('.conversion-review')).toBeNull();
  fireEvent.change(screen.getByLabelText('Normatyvo vienetas'),{target:{value:'100M'}});
  expect(screen.getByText('650 m → 6.5 × 100M')).toBeInTheDocument();
  expect(accept).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Patvirtinti konversiją'}));
  expect(accept).toHaveBeenCalledWith('100M');
});

it('Review Queue refetches confirmed historical knowledge after returning from history without changing the current row',async()=>{
  let reviewed=false;
  const candidate={id:'detector',version:1,description:'Historical detector wording',sistela_code:'N50-270',unit:'vnt.',system_type:'GSS',status:'CANDIDATE',evidence_type:'DERIVED',bulk_eligible:true,line_type:'Work'};
  mocks.api.mockImplementation(async(url:string)=>{
    if(url==='/projects')return [{id:'project',name:'Current GSS',system_type:'GSS'}];
    if(url==='/integration/capabilities'||url.endsWith('/imports'))return [];
    if(url.endsWith('/suggestions'))return reviewed?[confirmed,low]:[low];
    if(url.startsWith('/history/lines'))return {total:1,items:[{...candidate,status:reviewed?'CONFIRMED':'CANDIDATE'}]};
    if(url.endsWith('/lines'))return [line];
    if(url.endsWith('/validation'))return {status:'NEEDS_REVIEW',blocking:1,warnings:0,summary:{},statistics:{},rows:[{id:'line',category:'MISSING_SISTELA_CODE',issues:[{severity:'BLOCKING',message:'Confirm mapping'}],target_quantity:'28',target_unit:'vnt.',duplicates:[],price_status:'MISSING'}]};
    throw new Error(`Unexpected ${url}`);
  });
  mocks.post.mockImplementation(async(url:string)=>{if(url.endsWith('/automatic'))return [line];if(url==='/history/review'){reviewed=true;return {updated:1};}throw new Error(url);});
  const {container}=render(<App/>);
  await screen.findByRole('heading',{name:'Current GSS'});
  fireEvent.mouseDown(screen.getByRole('tab',{name:'Peržiūra'}),{button:0,ctrlKey:false});
  await screen.findByRole('heading',{name:'Peržiūra · Review Queue'});
  await waitFor(()=>expect(container.querySelector('.suggestion strong')).toHaveTextContent('N50-314'));
  fireEvent.click(screen.getByRole('button',{name:'Istorinės SISTELA sąmatos'}));
  await screen.findByText('Historical detector wording');
  fireEvent.click(screen.getByRole('button',{name:'Peržiūrėti'}));
  fireEvent.click(screen.getByRole('button',{name:'Patvirtinti kandidatą'}));
  await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/history/review',expect.objectContaining({status:'CONFIRMED'})));
  fireEvent.click(screen.getByRole('button',{name:/^Projektai/}));
  await waitFor(()=>expect(container.querySelector('.suggestion strong')).toHaveTextContent('N50-270'));
  expect(screen.getByText('Patvirtinta istorinė patirtis')).toBeInTheDocument();
  expect(screen.getByRole('button',{name:'Atverti šaltinį 1'})).toBeInTheDocument();
  expect(container.querySelector('.conversion-review')).toBeNull();
  expect(screen.getByText('Būsena: unmapped')).toBeInTheDocument();
  expect(mocks.api.mock.calls.filter(([url])=>url.endsWith('/suggestions')).length).toBeGreaterThanOrEqual(3);
});
