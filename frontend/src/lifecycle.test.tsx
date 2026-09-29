import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { App } from './App';
import { ApplicationControls, TrashScreen } from './Lifecycle';

const mocks=vi.hoisted(()=>({api:vi.fn(),post:vi.fn()}));
vi.mock('./api',()=>({api:mocks.api,post:mocks.post,apiUrl:(url:string)=>url}));
const project={id:'project',name:'Lifecycle GSS',system_type:'GSS'};
beforeEach(()=>{vi.clearAllMocks();mocks.api.mockResolvedValue([]);mocks.post.mockResolvedValue({});});
afterEach(cleanup);

it('moves a project only after dialog confirmation and removes it from active projects',async()=>{
  let trashed=false;
  mocks.api.mockImplementation(async(url:string)=>url==='/projects'?(trashed?[]:[project]):url==='/trash'?(trashed?[project]:[]):[]);
  mocks.post.mockImplementation(async()=>{trashed=true;return project;});
  render(<App/>);
  await screen.findByRole('heading',{name:project.name});
  fireEvent.click(screen.getByRole('button',{name:'Į šiukšlinę'}));
  expect(screen.getByRole('dialog',{name:'Perkelti projektą į šiukšlinę'})).toBeVisible();
  expect(mocks.post).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Atšaukti'}));
  expect(screen.queryByRole('dialog')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button',{name:'Į šiukšlinę'}));
  fireEvent.click(screen.getByRole('button',{name:'Perkelti į šiukšlinę'}));
  await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/projects/project/trash'));
  await screen.findByRole('heading',{name:'Šiukšlinė'});
  expect(screen.queryByRole('button',{name:/Lifecycle GSS GSS/})).not.toBeInTheDocument();
});

it('lists trash and restores a project, refreshing the normal list',async()=>{
  const changed=vi.fn().mockResolvedValue([]);
  mocks.api.mockResolvedValueOnce([project]).mockResolvedValue([]);
  render(<TrashScreen onChanged={changed}/>);
  fireEvent.click(await screen.findByRole('button',{name:'Atkurti'}));
  await screen.findByText('Projektas atkurtas.');
  expect(mocks.post).toHaveBeenCalledWith('/projects/project/restore',{});
  expect(changed).toHaveBeenCalledOnce();
  expect(screen.getByText('Šiukšlinė tuščia.')).toBeVisible();
});

it('permanent deletion requires the exact project name and an explicit action',async()=>{
  mocks.api.mockResolvedValueOnce([project]).mockResolvedValue([]);
  render(<TrashScreen onChanged={vi.fn().mockResolvedValue([])}/>);
  fireEvent.click(await screen.findByRole('button',{name:'Ištrinti visam laikui'}));
  const confirm=screen.getByRole('button',{name:'Patvirtinti galutinį ištrynimą'});
  expect(confirm).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Trinamo projekto pavadinimas'),{target:{value:'wrong'}});
  expect(confirm).toBeDisabled();
  fireEvent.change(screen.getByLabelText('Trinamo projekto pavadinimas'),{target:{value:project.name}});
  expect(confirm).toBeEnabled();expect(mocks.post).not.toHaveBeenCalled();
  fireEvent.click(confirm);
  await screen.findByText('Projektas ištrintas. Bendra istorija išsaugota.');
  expect(mocks.post).toHaveBeenCalledWith('/projects/project/delete',{confirmation:project.name});
});

it('shows deletion errors without losing the project or confirmation dialog',async()=>{
  mocks.api.mockResolvedValue([project]);mocks.post.mockRejectedValue(new Error('Failas užimtas'));
  render(<TrashScreen onChanged={vi.fn()}/>);
  fireEvent.click(await screen.findByRole('button',{name:'Ištrinti visam laikui'}));
  fireEvent.change(screen.getByLabelText('Trinamo projekto pavadinimas'),{target:{value:project.name}});
  fireEvent.click(screen.getByRole('button',{name:'Patvirtinti galutinį ištrynimą'}));
  expect(await screen.findByRole('alert')).toHaveTextContent('Failas užimtas');
  expect(screen.getByRole('dialog')).toBeVisible();
});

it('displays the runtime version and opens logs; shutdown waits for edits',async()=>{
  mocks.api.mockResolvedValue({version:'0.1.0',managed:true});const stopped=vi.fn();
  const {rerender}=render(<ApplicationControls busy={true} onStopped={stopped}/>);
  await screen.findByText('SISTELA Assistant 0.1.0');
  expect(screen.getByRole('button',{name:'Uždaryti programą'})).toBeDisabled();
  fireEvent.click(screen.getByRole('button',{name:'Atidaryti logų aplanką'}));
  expect(mocks.post).toHaveBeenCalledWith('/app/logs/open');
  rerender(<ApplicationControls busy={false} onStopped={stopped}/>);
  fireEvent.click(screen.getByRole('button',{name:'Uždaryti programą'}));
  await waitFor(()=>expect(stopped).toHaveBeenCalledOnce());
});
