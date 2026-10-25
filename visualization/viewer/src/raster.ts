import type { DatasetV1, FileIdentity, LayerV1 } from '../../layer-contract';

export const MANIFEST_SHA = '6b008eea5035a3749cb58de275a5c2f2f033dc62724c475ef72fb56f299b87f5';
export const EXPORT_ID = 'viewexport_b0ff6b261de6640dce02256a94340b4c1d1f390e85914ddb48ada08493ba6df1';
export const WIDTH = 360;
export const HEIGHT = 180;
export const RADIUS = 6371000;
export const PALETTE = { ocean: [21, 52, 74, 255], land: [107, 181, 151, 255], coast: [235, 211, 151, 255] } as const;
export const TRANSFORM = {
  sourceShape: [180, 360], sourceOrder: 'C; SOUTH_TO_NORTH; WEST_TO_EAST',
  displayShape: [180, 360], displayRow: '179 - sourceRow', displayColumn: 'sourceColumn',
  boundsDegrees: [-180, -90, 180, 90], periodicLongitude: true,
  seam: '+180 == -180; columns wrap modulo 360; no duplicate column',
  sampling: 'NEAREST; no resampling or interpolation',
  semantics: 'land_ocean_mask: 0=OCEAN,1=LAND; coastline_mask: 0=false,1=true; coastline color overrides base color',
  palette: PALETTE,
} as const;

export interface Manifest {
  schema: string; version: number; exportId: string; dataset: DatasetV1;
  arrays: { layerId: string; file: FileIdentity; dtypeDescr: string; order: string; shape: number[]; dataSha256: string }[];
  provenance: { inputs: FileIdentity[] };
  governance: Record<string, boolean>;
}
export interface TextureProvenance {
  schema: 'ARCANA_VIEW_T0_TEXTURE_V1'; status: 'DISPLAY_ONLY';
  manifestSha256: string; exportId: string;
  sourceArrays: FileIdentity[];
  transform: typeof TRANSFORM;
  texture: FileIdentity;
  rgbaSha256: string;
}

export function ensure(value: unknown, message: string): asserts value {
  if (!value) throw new Error(message);
}
export async function sha256(data: Uint8Array): Promise<string> {
  const hash = await crypto.subtle.digest('SHA-256', Uint8Array.from(data).buffer);
  return Array.from(new Uint8Array(hash), b => b.toString(16).padStart(2, '0')).join('');
}
export async function checkBytes(data: Uint8Array, expected: FileIdentity): Promise<void> {
  ensure(data.byteLength === expected.bytes, `Byte count mismatch: ${expected.path}`);
  ensure(await sha256(data) === expected.sha256, `SHA256 mismatch: ${expected.path}`);
}
export function selectedLayers(manifest: Manifest): [LayerV1, LayerV1] {
  ensure(manifest.schema === 'ARCANA_VIEW_STATIC_T0_EXPORT_V1' && manifest.version === 1 &&
    manifest.exportId === EXPORT_ID, 'Unrecognized export identity');
  const g = manifest.dataset.geometry;
  ensure(g.type === 'SPHERE' && g.radiusM === RADIUS && JSON.stringify(g.shape) === '[180,360]' &&
    g.rowOrder === 'SOUTH_TO_NORTH' && g.columnOrder === 'WEST_TO_EAST' && g.periodicLongitude,
    'Unsupported spherical grid');
  ensure(!manifest.dataset.scientificAuthorityPromoted && Object.values(manifest.governance).every(v => v === false),
    'Scientific authority mismatch');
  const source = manifest.provenance.inputs.find(x => x.path === 'external://R6_INITIAL_PHYSICAL_GEOGRAPHY.npz');
  ensure(source?.sha256 === 'a6edad24f639bd6283dc3dbd2a16306af5cda8e01152df2512231c9d5462506c' &&
    source.bytes === 1169900, 'Unverified original geography source');
  return ['land_ocean_mask', 'coastline_mask'].map(field => {
    const layers = manifest.dataset.layers.filter(x => x.id === `t0/${field}`);
    ensure(layers.length === 1, `Missing or ambiguous layer: ${field}`);
    const layer = layers[0];
    ensure(layer.numeric && layer.numeric.path === `arrays/t0__${field}.npy` && layer.field === field &&
      layer.dtype === 'uint8' && JSON.stringify(layer.shape) === '[180,360]' &&
      layer.authority === 'AUTHORIAL_SYNTHETIC_INITIALIZATION' && layer.sourceAuthority === 'DERIVED_AUTHORITY' &&
      layer.availability === 'VERIFIED' && layer.temporal.originMa === 210 &&
      JSON.stringify(layer.temporal.elapsedYears) === '[0]' && layer.temporal.interpolation === 'NONE' &&
      layer.source.sha256 === source.sha256, `Invalid T0 layer: ${field}`);
    const record = manifest.arrays.find(x => x.layerId === layer.id);
    ensure(record?.dtypeDescr === '|u1' && record.order === 'C' &&
      JSON.stringify(record.file) === JSON.stringify(layer.numeric), `Array record mismatch: ${field}`);
    return layer;
  }) as [LayerV1, LayerV1];
}

/** Only authenticated VIEW-1B uint8 masks. No eval/pickle or general scientific decoder. */
export function decodeMask(data: Uint8Array): Uint8Array {
  ensure(new TextDecoder('latin1').decode(data.subarray(1, 6)) === 'NUMPY' && data[0] === 0x93,
    'Invalid NPY magic');
  const major = data[6];
  ensure((major === 1 || major === 2) && data[7] === 0, 'Unsupported NPY version');
  const sizeBytes = major === 1 ? 2 : 4;
  ensure(data.length >= 8 + sizeBytes, 'Truncated NPY');
  const view = new DataView(data.buffer, data.byteOffset, data.byteLength);
  const size = sizeBytes === 2 ? view.getUint16(8, true) : view.getUint32(8, true);
  ensure(size < 65536 && data.length === 8 + sizeBytes + size + WIDTH * HEIGHT, 'Invalid NPY length');
  const header = new TextDecoder().decode(data.subarray(8 + sizeBytes, 8 + sizeBytes + size));
  ensure(/'descr':\s*'\|u1'/.test(header) && /'fortran_order':\s*False/.test(header) &&
    /'shape':\s*\(180,\s*360\)/.test(header), 'Unsupported mask shape/dtype/order');
  const values = data.slice(8 + sizeBytes + size);
  ensure(values.every(x => x === 0 || x === 1), 'Unsupported categorical mask value');
  return values;
}

export function cell(lat: number, lon: number): [number, number] {
  ensure(Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90, 'Invalid coordinate');
  return [Math.min(179, Math.floor(lat + 90)), Math.floor(((lon + 180) % 360 + 360) % 360)];
}
export function rgba(land: Uint8Array, coast: Uint8Array): Uint8Array {
  ensure(land.length === WIDTH * HEIGHT && coast.length === land.length, 'Mask shape mismatch');
  ensure(land.every(v => v === 0 || v === 1) && coast.every(v => v === 0 || v === 1), 'Unsupported category');
  const output = new Uint8Array(WIDTH * HEIGHT * 4);
  for (let row = 0; row < HEIGHT; row++) {
    for (let col = 0; col < WIDTH; col++) {
      const source = row * WIDTH + col;
      const pixel = ((179 - row) * WIDTH + col) * 4;
      output.set(coast[source] ? PALETTE.coast : land[source] ? PALETTE.land : PALETTE.ocean, pixel);
    }
  }
  return output;
}
export function checkProvenance(provenance: TextureProvenance, layers: [LayerV1, LayerV1]): void {
  ensure(provenance.schema === 'ARCANA_VIEW_T0_TEXTURE_V1' && provenance.status === 'DISPLAY_ONLY' &&
    provenance.manifestSha256 === MANIFEST_SHA && provenance.exportId === EXPORT_ID &&
    JSON.stringify(provenance.transform) === JSON.stringify(TRANSFORM) &&
    JSON.stringify(provenance.sourceArrays) === JSON.stringify(layers.map(l => l.numeric)) &&
    provenance.texture.path === 't0-display.png', 'Invalid texture provenance');
}
