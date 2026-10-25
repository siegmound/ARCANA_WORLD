import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { historical, formatTime, ordered, select, available, checkpoints, presentation, canPlay,
  zoomWindow, OLDEST, catalogFromVerifiedManifest, type TemporalState } from '../src/temporal';
import { sha256, MANIFEST_SHA, type Manifest } from '../src/raster';
import { createElement } from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import { Timeline } from '../src/Timeline';

const bytes = await readFile(new URL('../../exports/VIEW1B_T0_V1/manifest.json', import.meta.url));
assert.equal(await sha256(bytes), MANIFEST_SHA);
const manifest = JSON.parse(bytes.toString()) as Manifest;
const catalog = catalogFromVerifiedManifest(manifest);
const t0 = catalog.states[0];
const fixture = (id: string, years: number, change: Partial<TemporalState> = {}): TemporalState =>
  ({ ...t0, id, time: historical(years), ...change });

test('historical integer conversion and geological/fine time labels; rejects engineering time', () => {
  assert.equal(historical(210, 'Ma').years, OLDEST);
  assert.equal(historical(1.25, 'ka').years, 1250);
  assert.equal(formatTime(0), '0 ka'); assert.equal(formatTime(OLDEST), '210 Ma');
  assert.equal(formatTime(1), '0.001 ka');
  for (const v of [NaN, Infinity, -1, OLDEST + 1, .5]) assert.throws(() => historical(v));
  assert.throws(() => ordered([fixture('engineering', 0, { time: { kind: 'ENGINEERING_ELAPSED', years: 0 } as never })]));
});
test('actual catalog retains manifest identity, authority, masks, spatial support and source time', () => {
  assert.equal(catalog.states.length, 1); assert.equal(catalog.interpolation, 'NONE');
  assert.equal(t0.id, manifest.exportId); assert.equal(t0.manifestSha256, MANIFEST_SHA);
  assert.equal(t0.time.years, OLDEST); assert.equal(t0.branch, manifest.dataset.baseline.branch);
  assert.deepEqual(t0.layers, manifest.dataset.layers.filter(l => ['t0/land_ocean_mask', 't0/coastline_mask'].includes(l.id)));
  assert.deepEqual(t0.provenance, manifest.provenance); assert.ok(Object.isFrozen(t0.layers[0].validity));
  const bad: Manifest = { ...manifest, dataset: { ...manifest.dataset, layers: manifest.dataset.layers.map((l, i) =>
    i === 0 ? { ...l, temporal: { ...l.temporal, originMa: 209 } } : l) } };
  assert.throws(() => catalogFromVerifiedManifest(bad));
});
test('chronological order is oldest first, nonuniform exact checkpoints and deterministic ties', () => {
  const younger = fixture('z', 3), middle = fixture('m', 19_000), tie = fixture('a', 3);
  const states = [younger, t0, middle, tie];
  assert.deepEqual(ordered(states).map(s => s.id), [t0.id, 'm', 'a', 'z']);
  assert.equal(select(states, t0, 3)?.id, 'a');
  assert.equal(select([...states].reverse(), t0, 3)?.id, 'a');
  assert.throws(() => ordered([t0, t0]));
  assert.equal(checkpoints(states, t0, 18_000).previous?.id, 'm');
  assert.equal(checkpoints(states, t0, 18_000).next?.id, 'a');
});
test('unsupported epochs do not interpolate or substitute the rendered T0', () => {
  for (const age of [0, 1, 105_000_000, OLDEST - 1]) {
    assert.equal(select(catalog.states, t0, age), undefined);
    const view = presentation(catalog.states, t0, age, t0);
    assert.equal(view.available, false); assert.equal(view.selected, age);
    assert.equal(view.rendered?.time.years, OLDEST); assert.equal(view.retained, true);
  }
  assert.equal(presentation(catalog.states, t0, OLDEST, t0).retained, false);
  assert.equal(presentation(catalog.states, t0, 0).rendered, undefined);
});
test('unavailable/UNKNOWN, other histories, branches and resolutions never enter active scope', () => {
  const excluded = [fixture('unknown', 0, { availability: 'UNKNOWN' }),
    fixture('missing', 1, { availability: 'INPUT_UNAVAILABLE' }), fixture('unsupported', 2, { availability: 'UNSUPPORTED' }),
    fixture('legacy', 3, { history: 'R5' }), fixture('branch', 4, { branch: 'other' }),
    fixture('resolution', 5, { compatibility: 'DIFFERENT_GRID' })];
  assert.deepEqual(available([t0, ...excluded], t0), [t0]);
  assert.equal(canPlay([t0, ...excluded], t0), false);
});
test('single checkpoint disables playback and unavailable directional navigation', () => {
  assert.equal(canPlay(catalog.states, t0), false);
  assert.deepEqual(checkpoints(catalog.states, t0, OLDEST), { previous: undefined, next: undefined });
  assert.equal(checkpoints(catalog.states, t0, 0).previous, t0);
  assert.equal(checkpoints(catalog.states, t0, 0).next, undefined);
  assert.equal(canPlay([t0, fixture('same-epoch', OLDEST)], t0), false);
  assert.equal(canPlay([t0, fixture('future-fixture', 0)], t0), true);
});
test('time window zoom supports full history to single years without manufacturing states', () => {
  assert.deepEqual(zoomWindow(OLDEST, OLDEST), { older: OLDEST, younger: 0 });
  assert.deepEqual(zoomWindow(0, 1000), { older: 1000, younger: 0 });
  assert.deepEqual(zoomWindow(1250, 100), { older: 1300, younger: 1200 });
  assert.deepEqual(zoomWindow(10, 1), { older: 11, younger: 10 });
  assert.throws(() => zoomWindow(0, 0)); assert.throws(() => zoomWindow(0, NaN));
  assert.equal(catalog.states.length, 1);
});
test('timeline markup labels retained render separately and disables unsupported controls', () => {
  const render = (selected: number, loaded = true) => renderToStaticMarkup(createElement(Timeline, {
    catalog: loaded ? catalog : undefined, selected, rendered: loaded ? t0 : undefined, onSelect: () => {},
  }));
  const initial = render(OLDEST);
  for (const name of ['Previous checkpoint', 'Next checkpoint', 'Play historical checkpoints']) {
    assert.match(initial, new RegExp(`aria-label="${name}"[^>]*disabled=""`));
  }
  assert.match(initial, /Verified checkpoint available/);
  const unsupported = render(0);
  assert.match(unsupported, /aria-label="Selected time">0 ka/);
  assert.match(unsupported, /Last rendered state: 210 Ma/);
  assert.match(unsupported, /UNAVAILABLE · no verified dataset/);
  assert.match(unsupported, /data-selected-years="0" data-rendered-years="210000000"/);
  const unloaded = render(OLDEST, false);
  assert.match(unloaded, /No dataset rendered/);
  assert.doesNotMatch(unloaded, /Select T0/);
  const futureFixture = { ...catalog, states: [t0, fixture('future-test-only', 0)] };
  const future = (renderableIds: readonly string[]) => renderToStaticMarkup(createElement(Timeline, {
    catalog: futureFixture, selected: OLDEST, rendered: t0, onSelect: () => {}, renderableIds,
  }));
  assert.match(future([t0.id]), /aria-label="Play historical checkpoints"[^>]*disabled=""/);
  assert.doesNotMatch(future([t0.id, 'future-test-only']), /aria-label="Play historical checkpoints"[^>]*disabled=""/);
});
