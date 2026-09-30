import { afterEach, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { PdfDiagnostics, type PdfCandidate } from './PdfDiagnostics';

afterEach(cleanup);
const candidate: PdfCandidate = { id:'table-2-1', pages:[2,3], extraction_method:'geometry', row_count:12,
  score:.8, outcome:'CREDIBLE', inferred_columns:{UNIT:{index:2,confidence:.9}},
  score_reasons:[{code:'QUANTITY',weight:.24},{code:'ROOM_AREAS',weight:-.45}],
  preview:[{description:'Valdymo modulis',quantity:'2',unit:'vnt.'}] };

it('requires explicit confirmation with page, preview, roles and row count', () => {
  const select=vi.fn();
  render(<PdfDiagnostics options={{needs_selection:true,diagnostics:[candidate]}} busy={false} onSelect={select}/>);
  expect(screen.getByText('Radome galimą sąnaudų lentelę. Patvirtinkite.')).toBeVisible();
  expect(screen.getAllByText(/puslapiai 2, 3 · 12 eilučių/)[0]).toBeVisible();
  expect(screen.getAllByText(/Valdymo modulis — 2 vnt./)[0]).toBeVisible();
  expect(select).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole('button',{name:'Pasirinkti lentelę table-2-1'}));
  expect(select).toHaveBeenCalledWith('table-2-1');
});
it('shows ambiguity and disables actions while selection is saving', () => {
  render(<PdfDiagnostics options={{needs_selection:true,diagnostics:[candidate,{...candidate,id:'table-4-2',pages:[4]}]}} busy onSelect={vi.fn()}/>);
  expect(screen.getByText('Radome kelias galimas kiekių lenteles.')).toBeVisible();
  expect(screen.getAllByRole('button')).toHaveLength(2);
  for(const button of screen.getAllByRole('button')) expect(button).toBeDisabled();
});
it('retains rejected diagnostics without offering a selection', () => {
  render(<PdfDiagnostics options={{needs_selection:false,diagnostics:[{...candidate,outcome:'REJECTED'}]}} busy={false} onSelect={vi.fn()}/>);
  expect(screen.queryByRole('button')).not.toBeInTheDocument();
  fireEvent.click(screen.getByText('PDF importo diagnostika (1)'));
  fireEvent.click(screen.getByText('Vertinimo priežastys'));
  expect(screen.getByText('-0.450 ROOM_AREAS')).toBeVisible();
});
