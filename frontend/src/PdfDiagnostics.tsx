export interface PdfCandidate {
  id: string; pages: number[]; extraction_method: string; row_count: number;
  score: number; outcome: string; inferred_columns: Record<string, { index: number; confidence: number }>;
  score_reasons: { code: string; weight: number }[];
  preview: { description: string; quantity: string; unit: string }[];
}
export interface PdfOptions { needs_selection?: boolean; diagnostics?: PdfCandidate[] }

export function PdfDiagnostics({ options, busy, onSelect }: {
  options?: PdfOptions; busy: boolean; onSelect: (id: string) => void;
}) {
  if (!options?.diagnostics?.length) return null;
  const choices = options.diagnostics.filter(c => c.outcome === 'CREDIBLE');
  const candidateView = (c: PdfCandidate, selectable = false) => <article key={c.id} className="import-row">
    <strong>{c.id} · puslapiai {c.pages.join(', ')} · {c.row_count} eilučių</strong>
    <p>Metodas: {c.extraction_method} · įvertis {c.score.toFixed(2)} · {c.outcome}</p>
    <p>Stulpeliai: {Object.entries(c.inferred_columns).map(([role, v]) => `${role}: ${v.confidence.toFixed(2)}`).join(' · ')}</p>
    <ol>{c.preview.map((r, i) => <li key={i}>{r.description} — {r.quantity} {r.unit}</li>)}</ol>
    {selectable && <button className="primary" disabled={busy} onClick={() => onSelect(c.id)}>Pasirinkti lentelę {c.id}</button>}
    <details><summary>Vertinimo priežastys</summary>{c.score_reasons.map(r => <p key={r.code}>{r.weight > 0 ? '+' : ''}{r.weight.toFixed(3)} {r.code}</p>)}</details>
  </article>;
  return <section aria-label="PDF importo diagnostika">
    {options.needs_selection && <><h3>{choices.length > 1 ? 'Radome kelias galimas kiekių lenteles.' : 'Radome galimą sąnaudų lentelę. Patvirtinkite.'}</h3>
      <p>Eilutės bus pridėtos tik pasirinkus lentelę.</p>{choices.map(c => candidateView(c, true))}</>}
    <details><summary>PDF importo diagnostika ({options.diagnostics.length})</summary>{options.diagnostics.map(c => candidateView(c))}</details>
  </section>;
}
