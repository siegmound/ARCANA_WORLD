import { fileURLToPath } from 'node:url';
import { mkdir, writeFile, cp } from 'node:fs/promises';
import path from 'node:path';
import { stage } from './stage';

const viewer = path.resolve(fileURLToPath(new URL('..', import.meta.url)));
const visualization = path.dirname(viewer);
const dataset = path.join(visualization, 'exports', 'VIEW1B_T0_V1');
const publicRoot = path.join(viewer, 'public');
await mkdir(publicRoot, { recursive: true });
let availability: { status: string; error?: string };
try {
  await stage(dataset, visualization, path.join(publicRoot, 'arcana-t0'));
  availability = { status: 'VERIFIED' };
  console.log('VIEW2A_STAGE_VERIFIED — immutable source copy and DISPLAY_ONLY texture');
} catch (error) {
  availability = { status: 'UNAVAILABLE', error: String(error) };
  console.error(availability.error);
  if (!process.argv.includes('--allow-unavailable')) process.exitCode = 1;
}
await writeFile(path.join(publicRoot, 'arcana-availability.json'), JSON.stringify(availability, null, 2) + '\n');
// All Cesium dependencies are served locally; no CDN, ion token or online imagery.
for (const name of ['Assets', 'Workers', 'ThirdParty', 'Widgets']) {
  await cp(path.join(viewer, 'node_modules', 'cesium', 'Build', 'Cesium', name),
    path.join(publicRoot, 'cesium', name), { recursive: true, force: false, errorOnExist: false });
}
