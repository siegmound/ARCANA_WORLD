import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, mkdtemp, rename, rm, readdir } from 'node:fs/promises';
import path from 'node:path';
import { PNG } from 'pngjs';
import Ajv2020 from 'ajv/dist/2020.js';
import { MANIFEST_SHA, EXPORT_ID, TRANSFORM, WIDTH, HEIGHT, selectedLayers, decodeMask, rgba,
  checkBytes, checkProvenance, ensure, type Manifest, type TextureProvenance } from '../src/raster';

const hash = (bytes: Uint8Array) => createHash('sha256').update(bytes).digest('hex');
export async function stagedFiles(dataset: string, visualization: string): Promise<Map<string, Uint8Array>> {
  const manifestBytes = await readFile(path.join(dataset, 'manifest.json'));
  ensure(hash(manifestBytes) === MANIFEST_SHA, 'VIEW1B manifest SHA256 mismatch');
  const manifest = JSON.parse(manifestBytes.toString('utf8')) as Manifest;
  const schema = JSON.parse(await readFile(path.join(visualization, 'export-manifest.schema.json'), 'utf8'));
  const ajv = new Ajv2020({ allErrors: true, strict: true });
  const validate = ajv.compile(schema);
  ensure(validate(manifest), `VIEW1B schema validation failed: ${JSON.stringify(validate.errors)}`);
  const layers = selectedLayers(manifest);
  const result = new Map<string, Uint8Array>([['manifest.json', manifestBytes]]);
  const masks = [];
  for (const layer of layers) {
    ensure(layer.numeric, 'Missing numeric mask');
    const data = await readFile(path.join(dataset, layer.numeric.path));
    await checkBytes(data, layer.numeric);
    masks.push(decodeMask(data));
    result.set(layer.numeric.path, data);
  }
  const pixels = rgba(masks[0], masks[1]);
  const png = PNG.sync.write({ width: WIDTH, height: HEIGHT, data: Buffer.from(pixels) } as PNG,
    { colorType: 6, inputColorType: 6, bitDepth: 8, deflateLevel: 9, deflateStrategy: 3 });
  const provenance: TextureProvenance = {
    schema: 'ARCANA_VIEW_T0_TEXTURE_V1', status: 'DISPLAY_ONLY', manifestSha256: MANIFEST_SHA,
    exportId: EXPORT_ID, sourceArrays: layers.map(l => l.numeric!), transform: TRANSFORM,
    texture: { path: 't0-display.png', bytes: png.length, sha256: hash(png) }, rgbaSha256: hash(pixels),
  };
  checkProvenance(provenance, layers);
  const decoded = PNG.sync.read(png);
  ensure(decoded.width === WIDTH && decoded.height === HEIGHT && hash(decoded.data) === hash(pixels),
    'Derived PNG pixel mismatch');
  result.set('t0-display.png', png);
  result.set('texture-provenance.json', Buffer.from(JSON.stringify(provenance, null, 2) + '\n'));
  // Recheck sources after derivation; original outputs are read only.
  for (const [name, bytes] of result) {
    if (name === 'manifest.json' || name.endsWith('.npy')) {
      ensure(hash(await readFile(path.join(dataset, name))) === hash(bytes), `Source changed: ${name}`);
    }
  }
  return result;
}

export async function stage(dataset: string, visualization: string, destination: string): Promise<void> {
  ensure(process.platform === 'win32', 'Windows no-clobber publication required');
  const relative = path.relative(path.join(visualization, 'viewer'), destination);
  ensure(path.isAbsolute(destination) && relative !== '' && relative !== '..' &&
    !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative), 'Staging output outside viewer');
  const files = await stagedFiles(dataset, visualization);
  try {
    const entries = await readdir(destination);
    ensure(JSON.stringify(entries.sort()) === JSON.stringify(['arrays', 'manifest.json', 't0-display.png', 'texture-provenance.json']),
      'Existing stage file membership mismatch');
    ensure(JSON.stringify((await readdir(path.join(destination, 'arrays'))).sort()) ===
      JSON.stringify(['t0__coastline_mask.npy', 't0__land_ocean_mask.npy']), 'Existing stage array membership mismatch');
    for (const [name, data] of files) {
      ensure(hash(await readFile(path.join(destination, name))) === hash(data), `Existing stage mismatch: ${name}`);
    }
    return; // matching complete owned cache, never overwrite it
  } catch (error) {
    if (!(error instanceof Error && 'code' in error && error.code === 'ENOENT')) throw error;
  }
  await mkdir(path.dirname(destination), { recursive: true });
  const temporary = await mkdtemp(path.join(path.dirname(destination), '.arcana-stage-owned-'));
  let published = false;
  try {
    for (const [name, bytes] of files) {
      const target = path.join(temporary, name);
      await mkdir(path.dirname(target), { recursive: true });
      await writeFile(target, bytes, { flag: 'wx' });
      ensure(hash(await readFile(target)) === hash(bytes), `Staging hash mismatch: ${name}`);
    }
    await rename(temporary, destination);
    published = true;
  } finally {
    if (!published) {
      ensure(path.dirname(temporary) === path.dirname(destination) &&
        path.basename(temporary).startsWith('.arcana-stage-owned-'), 'Invalid cleanup ownership');
      await rm(temporary, { recursive: true });
    }
  }
}
