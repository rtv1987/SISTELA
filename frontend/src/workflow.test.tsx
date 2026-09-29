import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import { Cell, EstimateGrid } from './Grid';
import { EntryMode, entryReady, entryText } from './EntryMode';
import { parseTsv, pasteLines } from './ExcelPanel';
import { blankLine, type Line } from './types';

afterEach(cleanup);
const row = (changes: Partial<Line> = {}): Line => ({ ...blankLine('GSS'), line_type: 'Work',
  id: '1', project_id: 'project', source_position: '1', source_page: null, source_raw_text: '',
  confidence: null, mapping_status: 'unmapped', version: 1, sort_order: 0, entered_at: null, ...changes });

describe('editable grid', () => {
  it('saves on blur, keeping decimal text exact', async () => {
    const save = vi.fn().mockResolvedValue(undefined);
    render(<Cell value="1" label="Quantity" onSave={save}/>);
    fireEvent.change(screen.getByLabelText('Quantity'), { target: { value: '0.123456' } });
    expect(save).not.toHaveBeenCalled();
    fireEvent.blur(screen.getByLabelText('Quantity'));
    expect(save).toHaveBeenCalledWith('0.123456');
  });
  it('Escape discards the draft without saving', () => {
    const save = vi.fn().mockResolvedValue(undefined);
    render(<Cell value="old" label="Text" onSave={save}/>);
    const input = screen.getByLabelText('Text'); input.focus();
    fireEvent.change(input, { target: { value: 'discard' } });
    fireEvent.keyDown(input, { key: 'Escape' });
    expect(input).toHaveValue('old'); expect(save).not.toHaveBeenCalled();
  });
  it('restores the original value after a failed save', async () => {
    render(<Cell value="old" label="Text" onSave={() => Promise.reject(new Error('conflict'))}/>);
    fireEvent.change(screen.getByLabelText('Text'), { target: { value: 'new' } });
    fireEvent.blur(screen.getByLabelText('Text'));
    await waitFor(() => expect(screen.getByLabelText('Text')).toHaveValue('old'));
  });
  it('filters by review status and searches project descriptions', () => {
    render(<EstimateGrid lines={[row({project_description: 'Cable'}), row({id:'2', source_position:'2', line_type:'Material', project_description:'Sensor'})]} active="" onActive={vi.fn()} onEdit={vi.fn()} selection={{}} setSelection={vi.fn()}/>);
    fireEvent.change(screen.getByLabelText('Eilučių filtras'), {target:{value:'review'}});
    expect(screen.getByDisplayValue('Cable')).toBeInTheDocument();
    expect(screen.queryByDisplayValue('Sensor')).not.toBeInTheDocument();
    fireEvent.change(screen.getByLabelText('Ieškoti lentelėje'), {target:{value:'absent'}});
    expect(screen.queryByDisplayValue('Cable')).not.toBeInTheDocument();
  });
});

describe('Excel clipboard', () => {
  it('parses quoted tabs, line breaks and escaped quotes', () => {
    expect(parseTsv('"A\tB\n""C"""\tm\t1\r\n')).toEqual([['A\tB\n"C"','m','1']]);
  });
  it('preserves normative units and decimal precision', () => {
    const [value] = pasteLines('Kabelis\t100m\t0,123456', 'AS');
    expect(value).toMatchObject({unit:'100m', quantity:'0.123456', system_type:'AS', line_type:'Other'});
  });
  it.each(['"unclosed', 'Name\tm', 'Name\tm\tNaN', 'Name\tm\t-1', 'Name\tm\t1.1234567'])('rejects invalid paste %s', text => {
    expect(() => pasteLines(text, 'GSS')).toThrow();
  });
});

describe('manual Entry Mode', () => {
  it('requires explicit work confirmation and preserves 100m', () => {
    expect(entryReady(row())).toBe(false);
    const confirmed = row({mapping_status:'confirmed', sistela_code:'TEST', unit:'100m', quantity:'0.123456'});
    expect(entryReady(confirmed)).toBe(true);
    expect(entryText(confirmed)).toBe('TEST\tNauja eilutė\t100m\t0.123456');
    expect(entryReady(row({line_type:'Material'}))).toBe(true);
  });
  it('blocks marking unconfirmed work', () => {
    render(<EntryMode lines={[row()]} busy={false} onMark={vi.fn()} onReview={vi.fn()}/>);
    expect(screen.getByRole('button', {name:'Pažymėti suvestą'})).toBeDisabled();
  });
  it('copies values and submits explicit progress', async () => {
    const writeText = vi.fn().mockResolvedValue(undefined), mark = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'clipboard', {value:{writeText}, configurable:true});
    const value = row({line_type:'Material'});
    render(<EntryMode lines={[value]} busy={false} onMark={mark} onReview={vi.fn()}/>);
    fireEvent.click(screen.getByRole('button', {name:'Kopijuoti 4 laukus'}));
    await waitFor(() => expect(writeText).toHaveBeenCalledWith(entryText(value)));
    fireEvent.keyDown(window, {key:'Enter', ctrlKey:true});
    expect(mark).toHaveBeenCalledWith(value, true);
  });
});
