import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { cell, rgba, WIDTH, HEIGHT, PALETTE, decodeMask, checkBytes, sha256, selectedLayers,
  checkProvenance, type Manifest, type TextureProvenance } from '../src/raster';
import { stagedFiles } from '../scripts/stage';
import { PNG } from 'pngjs';

const visual = path.resolve(fileURLToPath(new URL('../..', import.meta.url)));
const dataset = path.join(visual, 'exports/VIEW1B_T0_V1');

test('all source cell centers map exactly; antimeridian wraps and poles remain supported', () => {
  for (let row = 0; row < HEIGHT; row++) for (let col = 0; col < WIDTH; col++) {
    assert.deepEqual(cell(-89.5 + row, -179.5 + col), [row, col]);
  }
  for (const longitude of [-540, -180, 180, 540]) assert.deepEqual(cell(0, longitude), [90, 0]);
  assert.deepEqual(cell(0, 179.999), [90, 359]);
  assert.deepEqual(cell(-90, -180), [0, 0]);
  assert.deepEqual(cell(90, 180), [179, 0]);
  assert.throws(() => cell(91, 0)); assert.throws(() => cell(0, Infinity));
});

test('north-first display reverses only rows and preserves corner categories', () => {
  const land = new Uint8Array(WIDTH * HEIGHT), coast = new Uint8Array(land.length);
  land[0] = 1; land[179 * WIDTH + 359] = 1; coast[179 * WIDTH] = 1;
  const pixels = rgba(land, coast);
  assert.deepEqual([...pixels.subarray(179 * WIDTH * 4, 179 * WIDTH * 4 + 4)], [...PALETTE.land]);
  assert.deepEqual([...pixels.subarray(359 * 4, 359 * 4 + 4)], [...PALETTE.land]);
  assert.deepEqual([...pixels.subarray(0, 4)], [...PALETTE.coast]);
  assert.deepEqual([...pixels.subarray(4, 8)], [...PALETTE.ocean]);
  assert.equal(pixels.length, 360 * 180 * 4); // no invented seam column
});

test('categorical zero is ocean, coastline is explicit, unsupported codes fail closed', () => {
  const land = new Uint8Array(WIDTH * HEIGHT), coast = new Uint8Array(land.length);
  assert.deepEqual([...rgba(land, coast).subarray(0, 4)], [...PALETTE.ocean]);
  land[0] = 2; assert.throws(() => rgba(land, coast), /category/);
  assert.throws(() => rgba(new Uint8Array(1), coast), /shape/);
});

test('actual VIEW1B masks and all 64800 PNG cells correspond byte-for-byte', async () => {
  const files = await stagedFiles(dataset, visual);
  const manifest = JSON.parse(new TextDecoder().decode(files.get('manifest.json'))) as Manifest;
  const layers = selectedLayers(manifest);
  const masks = layers.map(l => decodeMask(files.get(l.numeric!.path)!));
  assert.equal(masks[0].reduce((sum, v) => sum + v, 0), 14258);
  assert.equal(masks[1].reduce((sum, v) => sum + v, 0), 1049);
  const png = PNG.sync.read(Buffer.from(files.get('t0-display.png')!));
  assert.equal(png.width, WIDTH); assert.equal(png.height, HEIGHT);
  for (let row = 0; row < HEIGHT; row++) for (let col = 0; col < WIDTH; col++) {
    const i = row * WIDTH + col, p = ((179 - row) * WIDTH + col) * 4;
    const expected = masks[1][i] ? PALETTE.coast : masks[0][i] ? PALETTE.land : PALETTE.ocean;
    assert.deepEqual([...png.data.subarray(p, p + 4)], [...expected]);
  }
  assert.equal(png.data.length, 259200);
});

test('texture has DISPLAY_ONLY provenance and independent PNG/RGBA hashes', async () => {
  const files = await stagedFiles(dataset, visual);
  const manifest = JSON.parse(new TextDecoder().decode(files.get('manifest.json'))) as Manifest;
  const provenance = JSON.parse(new TextDecoder().decode(files.get('texture-provenance.json'))) as TextureProvenance;
  checkProvenance(provenance, selectedLayers(manifest));
  assert.equal(provenance.status, 'DISPLAY_ONLY');
  await checkBytes(files.get('t0-display.png')!, provenance.texture);
  const pixels = PNG.sync.read(Buffer.from(files.get('t0-display.png')!)).data;
  assert.equal(await sha256(pixels), provenance.rgbaSha256);
  provenance.status = 'PROMOTED' as TextureProvenance['status'];
  assert.throws(() => checkProvenance(provenance, selectedLayers(manifest)), /provenance/);
});

test('tampered array/hash/NPY header and altered source authority are rejected', async () => {
  const bytes = new Uint8Array(await readFile(path.join(dataset, 'arrays/t0__land_ocean_mask.npy')));
  const manifest = JSON.parse(await readFile(path.join(dataset, 'manifest.json'), 'utf8')) as Manifest;
  const layer = selectedLayers(manifest)[0];
  bytes[bytes.length - 1] ^= 1;
  await assert.rejects(checkBytes(bytes, layer.numeric!), /SHA256/);
  bytes[0] = 0; assert.throws(() => decodeMask(bytes), /magic/);
  const invalid = { ...manifest, dataset: { ...manifest.dataset,
    layers: manifest.dataset.layers.map(l => l.id === layer.id ? { ...l, authority: 'NONE' as const } : l) } };
  assert.throws(() => selectedLayers(invalid), /Invalid T0/);
});
