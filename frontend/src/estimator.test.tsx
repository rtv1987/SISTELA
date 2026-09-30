import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { EntryMode, entryReady, entryTarget, plainQuantity } from './EntryMode';
import { blankLine, type Line } from './types';

afterEach(cleanup);

const row=(changes:Partial<Line>={}):Line=>({...blankLine('GSS'),id:'a',project_id:'p',line_type:'Work',quantity:'650',unit:'m',sistela_code:'N50-210',mapping_status:'confirmed',source_position:'1',source_page:14,source_raw_text:'source',confidence:null,version:1,sort_order:1,entered_at:null,
  review_data:{conversion:{source_quantity:'650',source_unit:'m',target_quantity:'6.50',target_unit:'100m',confirmed_by_user:true}},...changes});

describe('Estimator handoff',()=>{
  it.each([['6,50','6.5'],['0.00000100','0.000001'],['650','650'],['1e-8','0.00000001']])('copies plain decimal %s',(input,expected)=>expect(plainQuantity(input)).toBe(expected));
  it('rejects stale conversion after source edit',()=>{
    expect(entryTarget(row()).quantity).toBe('6.50');
    expect(entryReady(row({quantity:'700'}))).toBe(false);
  });
  it('defaults to pending works and resumes first remaining work',()=>{
    render(<EntryMode worksOnly lines={[row({id:'material',line_type:'Material'}),row({id:'done',entered_at:'date'}),row({id:'next',project_description:'Next work'})]} busy={false} onMark={vi.fn()} onReview={vi.fn()}/>);
    expect(screen.getByRole('heading',{name:'Next work'})).toBeInTheDocument();
    expect(screen.getByText(/50%/)).toBeInTheDocument();
    expect(screen.getByLabelText('Suvedimo filtras')).toHaveValue('pending');
  });
  it('supports code quantity description enter space escape and avoids input shortcuts',async()=>{
    const writeText=vi.fn().mockResolvedValue(undefined);Object.defineProperty(navigator,'clipboard',{value:{writeText},configurable:true});
    const mark=vi.fn().mockResolvedValue(undefined), exit=vi.fn();
    const value=row({output_description:'Project wording'});
    render(<EntryMode worksOnly lines={[value]} busy={false} onMark={mark} onReview={vi.fn()} onExit={exit}/>);
    fireEvent.keyDown(window,{key:'c'});await waitFor(()=>expect(writeText).toHaveBeenLastCalledWith('N50-210'));
    fireEvent.keyDown(window,{key:'q'});await waitFor(()=>expect(writeText).toHaveBeenLastCalledWith('6.5'));
    fireEvent.keyDown(window,{key:'d'});await waitFor(()=>expect(writeText).toHaveBeenLastCalledWith('Project wording'));
    fireEvent.keyDown(window,{key:'Enter'});await waitFor(()=>expect(mark).toHaveBeenCalledWith(value,true));
    fireEvent.keyDown(window,{key:' '});await waitFor(()=>expect(mark).toHaveBeenCalledTimes(2));
    fireEvent.keyDown(screen.getByLabelText('Suvedimo filtras'),{key:'q'});expect(writeText).toHaveBeenCalledTimes(3);
    fireEvent.keyDown(window,{key:'Escape'});expect(exit).toHaveBeenCalledOnce();
  });
  it('navigates and filters reviewed works without changing entered flags',()=>{
    render(<EntryMode worksOnly lines={[row({id:'a',project_description:'First'}),row({id:'b',project_description:'Second',sistela_code:'',mapping_status:'needs_review'})]} busy={false} onMark={vi.fn()} onReview={vi.fn()}/>);
    fireEvent.keyDown(window,{key:'ArrowRight'});expect(screen.getByRole('heading',{name:'Second'})).toBeInTheDocument();
    fireEvent.keyDown(window,{key:'ArrowLeft'});expect(screen.getByRole('heading',{name:'First'})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Suvedimo filtras'),{target:{value:'review'}});expect(screen.getByRole('heading',{name:'Second'})).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Suvedimo filtras'),{target:{value:'confirmed'}});expect(screen.getByRole('heading',{name:'First'})).toBeInTheDocument();
  });
});
