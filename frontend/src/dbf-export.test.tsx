import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { DbfExport } from './DbfExport';

const mocks=vi.hoisted(()=>({api:vi.fn()}));
vi.mock('./api',()=>({api:mocks.api,apiUrl:(path:string)=>path}));
beforeEach(()=>{vi.clearAllMocks();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});

it('labels export experimental, limits it to clones and requires all six inputs',()=>{
  render(<DbfExport projectId="current"/>);
  fireEvent.click(screen.getByRole('button',{name:'Eksperimentinis DBF eksportas'}));
  expect(screen.getByText('Naudokite tik bandomai SISTELA sąmatai.')).toBeVisible();
  expect(screen.getByText(/Dabartinio projekto DBF eksportas blokuojamas/)).toBeVisible();
  const button=screen.getByRole('button',{name:'Atsisiųsti bandomąjį kloną ZIP'});
  expect(button).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Šeši originalaus archyvo DBF failai'),{target:{files:['sd','dd','nd','pd','td','od'].map(role=>new File(['fixture'],role+'25-04-14.dbf'))}});
  expect(button).toBeEnabled();
  expect(screen.queryByRole('button',{name:'Eksportuoti į SISTELA DBF'})).not.toBeInTheDocument();
});

it('displays actual project export blockers without invoking export',async()=>{
  mocks.api.mockResolvedValue({blockers:['CALCULATED_FIELDS_UNKNOWN']});
  render(<DbfExport projectId="current"/>);
  fireEvent.click(screen.getByRole('button',{name:'Eksperimentinis DBF eksportas'}));
  fireEvent.click(screen.getByRole('button',{name:'Tikrinti projekto DBF kliūtis'}));
  expect(await screen.findByRole('status')).toHaveTextContent('sumų perskaičiavimas');
  expect(screen.getByText('CALCULATED_FIELDS_UNKNOWN')).toBeInTheDocument();
  expect(mocks.api).toHaveBeenCalledWith('/projects/current/dbf/plan');
});

it('does not claim success when DBF validation fails',async()=>{
  const fetch=vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:'Schema neatitinka'})});vi.stubGlobal('fetch',fetch);
  render(<DbfExport projectId="current"/>);
  fireEvent.click(screen.getByRole('button',{name:'Eksperimentinis DBF eksportas'}));
  fireEvent.change(screen.getByLabelText('Šeši originalaus archyvo DBF failai'),{target:{files:Array.from({length:6},(_,i)=>new File(['bad'],`${i}.dbf`))}});
  fireEvent.click(screen.getByRole('button',{name:'Atsisiųsti bandomąjį kloną ZIP'}));
  await waitFor(()=>expect(screen.getByRole('status')).toHaveTextContent('Schema neatitinka'));
  expect(fetch).toHaveBeenCalledWith('/dbf/clone',expect.objectContaining({method:'POST'}));
});
