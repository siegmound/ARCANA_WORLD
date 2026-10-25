import { MANIFEST_SHA, WIDTH, HEIGHT, selectedLayers, checkBytes, decodeMask, rgba, sha256,
  checkProvenance, ensure, type Manifest, type TextureProvenance } from './raster';

async function local(path: string): Promise<Uint8Array> {
  const response = await fetch(`/arcana-t0/${path}`, { cache: 'no-store' });
  ensure(response.ok, `Local dataset unavailable: ${path} (${response.status})`);
  return new Uint8Array(await response.arrayBuffer());
}

export async function loadDataset(): Promise<{ manifest: Manifest; textureUrl: string; provenance: TextureProvenance }> {
  const availability = await fetch('/arcana-availability.json', { cache: 'no-store' });
  ensure(availability.ok, 'Local dataset has not been staged');
  const state = await availability.json() as { status: string; error?: string };
  ensure(state.status === 'VERIFIED', state.error ?? 'Local dataset unavailable');
  const manifestBytes = await local('manifest.json');
  ensure(await sha256(manifestBytes) === MANIFEST_SHA, 'VIEW1B manifest SHA256 mismatch');
  const manifest = JSON.parse(new TextDecoder().decode(manifestBytes)) as Manifest;
  const layers = selectedLayers(manifest);
  const masks = await Promise.all(layers.map(async layer => {
    ensure(layer.numeric, 'Missing source array');
    const bytes = await local(layer.numeric.path);
    await checkBytes(bytes, layer.numeric);
    return decodeMask(bytes);
  }));
  const bytes = await local('t0-display.png');
  const provenance = JSON.parse(new TextDecoder().decode(await local('texture-provenance.json'))) as TextureProvenance;
  checkProvenance(provenance, layers);
  await checkBytes(bytes, provenance.texture);
  const expected = rgba(masks[0], masks[1]);
  ensure(await sha256(expected) === provenance.rgbaSha256, 'Texture/source RGBA mismatch');
  const blob = new Blob([Uint8Array.from(bytes).buffer], { type: 'image/png' });
  const bitmap = await createImageBitmap(blob, { colorSpaceConversion: 'none', premultiplyAlpha: 'none' });
  try {
    ensure(bitmap.width === WIDTH && bitmap.height === HEIGHT, 'Display texture shape mismatch');
    const canvas = document.createElement('canvas');
    canvas.width = WIDTH; canvas.height = HEIGHT;
    const context = canvas.getContext('2d', { willReadFrequently: true });
    ensure(context, 'Texture validation canvas unavailable');
    context.imageSmoothingEnabled = false;
    context.drawImage(bitmap, 0, 0);
    const actual = new Uint8Array(context.getImageData(0, 0, WIDTH, HEIGHT).data);
    ensure(actual.every((v, i) => v === expected[i]), 'Decoded PNG differs from source categorical cells');
  } finally {
    bitmap.close();
  }
  return { manifest, provenance, textureUrl: URL.createObjectURL(blob) };
}
