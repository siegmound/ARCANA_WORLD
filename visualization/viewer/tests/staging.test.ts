import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, readdir, mkdir, writeFile, mkdtemp, rm } from 'node:fs/promises';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { stage, stagedFiles } from '../scripts/stage';

const viewer = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const visual = path.dirname(viewer);
const dataset = path.join(visual, 'exports/VIEW1B_T0_V1');
const hash = (data: Uint8Array) => createHash('sha256').update(data).digest('hex');

test('derivation is repeatable and original VIEW1B files remain unchanged', async () => {
  const names = ['manifest.json', 'arrays/t0__land_ocean_mask.npy', 'arrays/t0__coastline_mask.npy'];
  const before = await Promise.all(names.map(async n => hash(await readFile(path.join(dataset, n)))));
  const first = await stagedFiles(dataset, visual), second = await stagedFiles(dataset, visual);
  assert.equal(first.size, 5);
  for (const [name, bytes] of first) assert.deepEqual(bytes, second.get(name));
  assert.deepEqual(before, await Promise.all(names.map(async n => hash(await readFile(path.join(dataset, n))))));
});

test('fresh staging, validated reuse and failures never overwrite existing evidence', async () => {
  const owned = await mkdtemp(path.join(viewer, '.test-owned-'));
  try {
    const target = path.join(owned, 'stage');
    await stage(dataset, visual, target);
    const before = hash(await readFile(path.join(target, 'texture-provenance.json')));
    await stage(dataset, visual, target);
    assert.equal(before, hash(await readFile(path.join(target, 'texture-provenance.json'))));
    const sentinel = path.join(owned, 'existing');
    await mkdir(sentinel); await writeFile(path.join(sentinel, 'sentinel'), 'preserve');
    await assert.rejects(stage(dataset, visual, sentinel));
    assert.equal(await readFile(path.join(sentinel, 'sentinel'), 'utf8'), 'preserve');
    await assert.rejects(stage(path.join(owned, 'missing'), visual, path.join(owned, 'never-published')));
    assert.deepEqual((await readdir(owned)).sort(), ['existing', 'stage']);
    const invalid = path.join(owned, 'invalid'); await mkdir(invalid);
    await writeFile(path.join(invalid, 'manifest.json'), '{}');
    await assert.rejects(stage(invalid, visual, path.join(owned, 'invalid-never-published')), /SHA256/);
  } finally {
    assert.equal(path.dirname(owned), viewer);
    assert.ok(path.basename(owned).startsWith('.test-owned-'));
    await rm(owned, { recursive: true });
  }
});
