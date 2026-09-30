import { useEffect, useMemo, useRef, useState } from 'react';
import { flexRender, getCoreRowModel, getFilteredRowModel, getSortedRowModel, useReactTable, type ColumnDef, type RowSelectionState, type SortingState } from '@tanstack/react-table';
import Decimal from 'decimal.js';
import { Search, ArrowUpDown } from 'lucide-react';
import { type Line, typeLabel } from './types';

export function Cell({ value, label, options, onSave }: { value: string; label: string; options?: string[]; onSave: (v: string) => Promise<void> }) {
  const [draft, setDraft] = useState(value);
  const cancel = useRef(false);
  useEffect(() => setDraft(value), [value]);
  const save = () => { if (cancel.current) { cancel.current = false; return; } if (draft !== value) void onSave(draft).catch(() => setDraft(value)); };
  if (options) return <select aria-label={label} value={draft} onChange={e => { setDraft(e.target.value); void onSave(e.target.value).catch(() => setDraft(value)); }}>{options.map(o => <option key={o} value={o}>{o in typeLabel ? typeLabel[o as keyof typeof typeLabel] : o}</option>)}</select>;
  return <input aria-label={label} title={draft} value={draft} onChange={e => setDraft(e.target.value)} onBlur={save} onKeyDown={e => {
    if (e.key === 'Enter') { e.preventDefault(); e.currentTarget.blur(); const row = e.currentTarget.closest('tr'); const next = row?.nextElementSibling?.querySelector<HTMLInputElement>('input[data-edit]'); next?.focus(); }
    if (e.key === 'Escape') { cancel.current = true; setDraft(value); e.currentTarget.blur(); }
  }} data-edit="true" />;
}

export function EstimateGrid({ lines, active, onActive, onEdit, selection, setSelection }: {
  lines: Line[]; active: string; onActive: (id: string) => void;
  onEdit: (id: string, field: string, value: string | null) => Promise<void>;
  selection: RowSelectionState; setSelection: (value: RowSelectionState | ((old: RowSelectionState) => RowSelectionState)) => void;
}) {
  const [search, setSearch] = useState(''); const [type, setType] = useState('');
  const [group, setGroup] = useState('line_type'); const [sorting, setSorting] = useState<SortingState>([]);
  const data = useMemo(() => lines.filter(l => !type || (type === 'review' ? l.line_type === 'Work' && !l.sistela_code : l.line_type === type)), [lines, type]);
  const columns = useMemo<ColumnDef<Line>[]>(() => {
    const edit = (key: keyof Line, title: string, width: number, options?: string[]): ColumnDef<Line> => ({
      accessorKey: key, header: title, size: width,
      sortingFn: ['quantity','material_price','work_price'].includes(key) ? (a, b) => new Decimal(String(a.original[key] ?? 0)).cmp(String(b.original[key] ?? 0)) : 'alphanumeric',
      cell: ({ row }) => <><Cell value={String(row.original[key] ?? '')} label={`${title} ${row.original.source_position || row.index + 1}`} options={options} onSave={v => onEdit(row.original.id, key, ['material_price','work_price'].includes(key) && !v ? null : ['quantity','material_price','work_price'].includes(key) ? v.replace(',', '.') : v)} />{key==='sistela_code'&&row.original.sistela_code&&<small>{row.original.review_data?.suggestion?.origin==='catalog'?'Normatyvų katalogas':row.original.review_data?.suggestion?.catalog_verified?'Istorija + katalogas':row.original.review_data?.code_type==='custom'?'Vartotojo kodas':row.original.review_data?.automatic?'Istorinis atitikmuo':'Vartotojo pasirinkimas'}</small>}</>,
    });
    return [
      { id: 'select', size: 38, header: ({ table }) => <input type="checkbox" aria-label="Pažymėti matomas eilutes" checked={table.getIsAllRowsSelected()} onChange={table.getToggleAllRowsSelectedHandler()} />, cell: ({ row }) => <input type="checkbox" aria-label={`Pažymėti eilutę ${row.index + 1}`} checked={row.getIsSelected()} onChange={row.getToggleSelectedHandler()} /> },
      { accessorKey: 'source_position', header: '#', size: 42 },
      { accessorKey: 'mapping_status', header: 'Būsena', size: 120, cell: ({ row }) => <span className={`status ${row.original.mapping_status}`}>{row.original.mapping_status === 'confirmed' ? 'Patvirtinta' : row.original.mapping_status === 'suggested' ? 'Pasiūlyta' : row.original.sistela_code ? 'Su kodu' : row.original.line_type === 'Work' ? 'Reikia kodo' : 'Peržiūrėti'}</span> },
      edit('project_description', 'Projekto pavadinimas', 310), edit('technical_reference', 'Modelis / žymuo', 145),
      edit('unit', 'Vnt.', 80), edit('quantity', 'Kiekis', 90), edit('sistela_code', 'SISTELA kodas', 135),
      edit('output_description', 'Galutinis pavadinimas', 290), edit('system_type', 'Sistema', 90),
      edit('line_type', 'Tipas', 125, ['Material','Work','Other']), edit('material_price', 'Medž. kaina €', 125),
      edit('work_price', 'Darbo kaina €', 125), edit('sistela_original_description', 'Originalus normatyvo pavadinimas', 300),
      { accessorKey: 'confidence', header: 'Atitikimas', size: 105, cell: ({ getValue }) => { const v = getValue<string | null>(); return v === null ? '—' : new Decimal(v).gte('.9') ? 'High' : new Decimal(v).gte('.7') ? 'Medium' : 'Low'; } },
      edit('notes', 'Pastabos', 250),
    ];
  }, [onEdit]);
  const table = useReactTable({ data, columns, getRowId: row => row.id, state: { globalFilter: search, sorting, rowSelection: selection }, onSortingChange: setSorting, onRowSelectionChange: setSelection, enableRowSelection: true, getCoreRowModel: getCoreRowModel(), getFilteredRowModel: getFilteredRowModel(), getSortedRowModel: getSortedRowModel() });
  const rows = table.getRowModel().rows;
  const groups = new Map<string, typeof rows>();
  for (const row of rows) { const key = group === 'line_type' ? typeLabel[row.original.line_type] : group === 'system_type' ? row.original.system_type : ''; groups.set(key, [...(groups.get(key) || []), row]); }
  return <section className="grid-section">
    <div className="filterbar"><div className="search"><Search size={16}/><input aria-label="Ieškoti lentelėje" placeholder="Ieškoti pavadinimo, modelio, kodo…" value={search} onChange={e => setSearch(e.target.value)}/></div>
      <select aria-label="Eilučių filtras" value={type} onChange={e => setType(e.target.value)}><option value="">Visos eilutės</option><option value="Material">Medžiagos</option><option value="Work">Darbai</option><option value="review">Darbai be kodo</option></select>
      <select aria-label="Grupavimas" value={group} onChange={e => setGroup(e.target.value)}><option value="line_type">Grupuoti pagal tipą</option><option value="system_type">Grupuoti pagal sistemą</option><option value="">Negrupuoti</option></select><span>{rows.length} eilučių</span>
    </div>
    <div className="table-scroll"><table className="estimate-table" style={{ width: table.getTotalSize() }}>
      <thead>{table.getHeaderGroups().map(h => <tr key={h.id}>{h.headers.map(header => <th key={header.id} style={{ width: header.getSize() }}>{header.column.getCanSort() ? <button onClick={header.column.getToggleSortingHandler()}>{flexRender(header.column.columnDef.header, header.getContext())}<ArrowUpDown size={11}/></button> : flexRender(header.column.columnDef.header, header.getContext())}</th>)}</tr>)}</thead>
      {[...groups].map(([label, members]) => <tbody key={label}>{label && <tr className="group-row"><td colSpan={columns.length}>{label}<span>{members.length}</span></td></tr>}{members.map(row => <tr key={row.id} className={`${active === row.id ? 'active-row' : ''} ${row.getIsSelected() ? 'selected-row' : ''}`} onClick={() => onActive(row.id)}>{row.getVisibleCells().map(cell => <td key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</td>)}</tr>)}</tbody>)}
    </table>{!rows.length && <div className="empty-grid">Eilučių nėra. Importuokite dokumentą arba pridėkite eilutę.</div>}</div>
    <footer className="grid-footer"><span>Tab – kitas laukas · Enter – kita eilutė · Išsaugoma palikus lauką</span><span>{Object.values(selection).filter(Boolean).length} pažymėta</span></footer>
  </section>;
}
