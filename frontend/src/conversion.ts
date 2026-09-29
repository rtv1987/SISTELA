// A known normative target is mandatory; never choose a target by default.
export function conversionFactor(source: string, target: string): string | null {
  const normalize = (unit: string) => unit.normalize('NFKC').toLowerCase().replace(/\s+/g, '');
  const from = normalize(source), to = normalize(target);
  if (from === 'm' && to === '100m') return '0.01';
  if (from === '100m' && to === 'm') return '100';
  return null;
}
