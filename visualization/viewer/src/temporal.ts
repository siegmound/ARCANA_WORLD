import { ensure, selectedLayers, MANIFEST_SHA, type Manifest } from './raster';

export const OLDEST = 210_000_000;
export type HistoricalTime = Readonly<{ kind: 'HISTORICAL_BP'; years: number }>;
export interface TemporalState {
  readonly id: string;
  readonly time: HistoricalTime;
  readonly history: string;
  readonly branch: string;
  readonly compatibility: string;
  readonly availability: 'VERIFIED' | 'INPUT_UNAVAILABLE' | 'UNKNOWN' | 'UNSUPPORTED';
  readonly manifestSha256: string;
  readonly provenance: Manifest['provenance'];
  readonly layers: Manifest['dataset']['layers'];
  readonly geometry: Manifest['dataset']['geometry'];
  readonly checkpoint: Readonly<{ label: string; events: readonly string[] }>;
}
export interface TemporalCatalog {
  readonly schema: 'ARCANA_VIEW_TEMPORAL_CATALOG_V1';
  readonly timeAxis: 'HISTORICAL_BP';
  readonly interpolation: 'NONE';
  readonly states: readonly TemporalState[];
}
export function historical(value: number, unit: 'Ma' | 'ka' | 'years' = 'years'): HistoricalTime {
  const years = value * (unit === 'Ma' ? 1_000_000 : unit === 'ka' ? 1_000 : 1);
  ensure(Number.isSafeInteger(years) && years >= 0 && years <= OLDEST, 'Invalid historical time');
  return Object.freeze({ kind: 'HISTORICAL_BP', years });
}
export function formatTime(years: number): string {
  historical(years);
  if (years >= 1_000_000) return `${years / 1_000_000} Ma`;
  return `${years / 1_000} ka`;
}
export function ordered(states: readonly TemporalState[]): readonly TemporalState[] {
  states.forEach(s => { ensure(s.time.kind === 'HISTORICAL_BP', 'Engineering time is not historical time'); historical(s.time.years); });
  ensure(new Set(states.map(s => s.id)).size === states.length, 'Duplicate temporal dataset identity');
  return [...states].sort((a, b) => b.time.years - a.time.years || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0));
}
export function available(states: readonly TemporalState[], scope: TemporalState): readonly TemporalState[] {
  return ordered(states).filter(s => s.availability === 'VERIFIED' && s.history === scope.history &&
    s.branch === scope.branch && s.compatibility === scope.compatibility);
}
/** Exact match only. No nearest state, interpolation, temporal tolerance or cross-history fallback. */
export function select(states: readonly TemporalState[], scope: TemporalState, years: number): TemporalState | undefined {
  historical(years);
  return available(states, scope).find(s => s.time.years === years);
}
export function checkpoints(states: readonly TemporalState[], scope: TemporalState, years: number) {
  historical(years);
  const list = available(states, scope);
  return { previous: [...list].reverse().find(s => s.time.years > years), next: list.find(s => s.time.years < years) };
}
export function presentation(states: readonly TemporalState[], scope: TemporalState, selected: number, rendered?: TemporalState) {
  const exact = select(states, scope, selected);
  return { selected, available: !!exact, rendered, retained: !!rendered && rendered.time.years !== selected };
}
export function canPlay(states: readonly TemporalState[], scope: TemporalState): boolean {
  return new Set(available(states, scope).map(s => s.time.years)).size > 1;
}
export interface TimeWindow { readonly older: number; readonly younger: number }
export function zoomWindow(selected: number, span: number): TimeWindow {
  historical(selected);
  ensure(Number.isSafeInteger(span) && span > 0, 'Invalid time window');
  const width = Math.min(OLDEST, span);
  const younger = Math.max(0, Math.min(OLDEST - width, selected - Math.floor(width / 2)));
  return { older: younger + width, younger };
}
/** Called only after the browser has authenticated the manifest and both displayed arrays. */
export function catalogFromVerifiedManifest(manifest: Manifest): TemporalCatalog {
  const layers = selectedLayers(manifest);
  const state: TemporalState = {
    id: manifest.exportId, time: historical(layers[0].temporal.originMa, 'Ma'),
    history: `R6_INITIAL_WORLD:${manifest.dataset.baseline.head}`,
    branch: manifest.dataset.baseline.branch,
    compatibility: 'R6_SPHERE_6371000_180x360_CATEGORICAL_T0_V1',
    availability: 'VERIFIED', manifestSha256: MANIFEST_SHA,
    provenance: manifest.provenance, layers, geometry: manifest.dataset.geometry,
    checkpoint: { label: 'T0 · initial world', events: [] },
  };
  // Deep freeze a detached snapshot; no caller can mutate the export through the catalog.
  const freeze = (value: unknown): void => {
    if (value && typeof value === 'object') { Object.values(value).forEach(freeze); Object.freeze(value); }
  };
  const catalog: TemporalCatalog = structuredClone({ schema: 'ARCANA_VIEW_TEMPORAL_CATALOG_V1',
    timeAxis: 'HISTORICAL_BP', interpolation: 'NONE', states: [state] });
  freeze(catalog);
  return catalog;
}
