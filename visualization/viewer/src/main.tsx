import { useEffect, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CesiumWidget, EllipsoidTerrainProvider, Globe, SingleTileImageryProvider, ImageryLayer,
  TextureMinificationFilter, TextureMagnificationFilter, Ion } from '@cesium/engine';
import { Ellipsoid, GeographicProjection, Cartesian3, Math as CesiumMath, Color, Rectangle } from '@cesium/core';
import 'cesium/Build/Cesium/Widgets/widgets.css';
import './style.css';
import { loadDataset } from './dataset';
import { EXPORT_ID, RADIUS } from './raster';
import { Timeline } from './Timeline';
import { OLDEST, formatTime, catalogFromVerifiedManifest, type TemporalCatalog } from './temporal';

type Status = 'LOADING' | 'VERIFIED' | 'ERROR';
const RENDERABLE_IDS = Object.freeze([EXPORT_ID]);

function App() {
  const container = useRef<HTMLDivElement>(null);
  const viewer = useRef<CesiumWidget | null>(null);
  const imagery = useRef<ImageryLayer | null>(null);
  const [status, setStatus] = useState<Status>('LOADING');
  const [message, setMessage] = useState('Authenticating local T0 dataset…');
  const [visible, setVisible] = useState(true);
  const [attempt, setAttempt] = useState(0);
  const [catalog, setCatalog] = useState<TemporalCatalog>();
  const [selected, setSelected] = useState(OLDEST);
  useEffect(() => {
    document.title = `ARCANA World — selected ${formatTime(selected)} · ${status === 'VERIFIED' ? 'rendered 210 Ma' : 'no rendered dataset'}`;
  }, [selected, status]);

  useEffect(() => {
    if (!container.current) return;
    let disposed = false;
    let failed = false;
    let textureUrl: string | undefined;
    let removePostRender: (() => void) | undefined;
    const element = container.current;
    const sphere = new Ellipsoid(RADIUS, RADIUS, RADIUS);
    let globeViewer: CesiumWidget;
    const fail = (error: unknown) => {
      if (disposed) return;
      failed = true;
      setCatalog(undefined);
      const detail = error instanceof Error ? error.message.split('\n')[0] : String(error);
      setStatus('ERROR'); setMessage(detail.replace(/blob:[^ ]+/g, 'the verified display texture'));
      if (viewer.current && !viewer.current.isDestroyed()) {
        viewer.current.imageryLayers.removeAll(); imagery.current = null;
        viewer.current.scene.requestRender();
      }
      element.dataset.renderStatus = 'ERROR';
    };
    try {
      Ion.defaultAccessToken = '';
      globeViewer = new CesiumWidget(element, {
        ellipsoid: sphere, globe: new Globe(sphere), mapProjection: new GeographicProjection(sphere),
        terrainProvider: new EllipsoidTerrainProvider({ ellipsoid: sphere }),
        baseLayer: false, skyBox: false,
        skyAtmosphere: false, scene3DOnly: true, requestRenderMode: true,
        shouldAnimate: false, maximumRenderTimeChange: Infinity,
      });
      viewer.current = globeViewer;
      globeViewer.scene.backgroundColor = Color.fromCssColorString('#08131d');
      globeViewer.scene.globe.baseColor = Color.fromCssColorString('#263d48');
      globeViewer.scene.globe.enableLighting = false;
      globeViewer.scene.globe.showGroundAtmosphere = false;
      globeViewer.scene.fog.enabled = false;
      if (globeViewer.scene.sun) globeViewer.scene.sun.show = false;
      if (globeViewer.scene.moon) globeViewer.scene.moon.show = false;
      globeViewer.scene.screenSpaceCameraController.minimumZoomDistance = RADIUS * 0.02;
      globeViewer.scene.screenSpaceCameraController.maximumZoomDistance = RADIUS * 6;
      globeViewer.camera.setView({ destination: Cartesian3.fromDegrees(-70, 15, RADIUS * 2.1, sphere),
        orientation: { heading: 0, pitch: -CesiumMath.PI_OVER_TWO, roll: 0 } });
      element.dataset.radius = JSON.stringify(sphere.radii);
      element.dataset.renderStatus = 'LOADING';
      globeViewer.scene.renderError.addEventListener((_scene, error) => fail(error));
    } catch (error) {
      fail(error);
      return;
    }
    const recordTransport = () => {
      const resources = performance.getEntriesByType('resource').map(entry => new URL(entry.name, location.href));
      element.dataset.resourceOrigins = JSON.stringify([...new Set(resources.map(url => url.origin))]);
      element.dataset.externalResources = JSON.stringify(resources.filter(url =>
        url.origin !== location.origin && url.protocol !== 'data:' && url.protocol !== 'blob:').map(url => url.href));
    };
    const transport = new PerformanceObserver(recordTransport);
    transport.observe({ type: 'resource', buffered: true });
    const blockedResource = (event: SecurityPolicyViolationEvent) => {
      element.dataset.blockedResource = event.blockedURI;
      if (/^https?:/.test(event.blockedURI) && new URL(event.blockedURI).origin !== location.origin) {
        fail(new Error('External resource request blocked; local-only rendering required'));
      }
    };
    document.addEventListener('securitypolicyviolation', blockedResource);
    recordTransport();
    setStatus('LOADING'); setMessage('Authenticating local T0 dataset…');
    setCatalog(undefined);
    void loadDataset().then(async data => {
      textureUrl = data.textureUrl;
      if (disposed) { URL.revokeObjectURL(textureUrl); return; }
      const provider = await SingleTileImageryProvider.fromUrl(textureUrl, {
        rectangle: Rectangle.MAX_VALUE, ellipsoid: sphere,
      });
      if (disposed) return;
      const layer = new ImageryLayer(provider, {
        minificationFilter: TextureMinificationFilter.NEAREST,
        magnificationFilter: TextureMagnificationFilter.NEAREST, maximumAnisotropy: 1,
      });
      provider.errorEvent.addEventListener(error => fail(error.message));
      globeViewer.imageryLayers.add(layer); imagery.current = layer;
      element.dataset.minification = String(layer.minificationFilter);
      element.dataset.magnification = String(layer.magnificationFilter);
      element.dataset.pixelVerification = '64800_SOURCE_CELLS_EXACT';
      element.dataset.exportId = data.manifest.exportId;
      let frames = 0;
      removePostRender = globeViewer.scene.postRender.addEventListener(() => {
        if (disposed || failed) return;
        frames++;
        element.dataset.renderFrames = String(frames);
        element.dataset.camera = JSON.stringify({ position: globeViewer.camera.positionWC,
          heading: globeViewer.camera.heading, pitch: globeViewer.camera.pitch });
        if (globeViewer.scene.globe.tilesLoaded && frames >= 3) {
          element.dataset.renderStatus = 'VERIFIED';
          setStatus('VERIFIED'); setMessage('T0 geography verified · local dataset');
          setCatalog(current => current ?? catalogFromVerifiedManifest(data.manifest));
        }
        if (frames < 4) globeViewer.scene.requestRender();
      });
      globeViewer.scene.requestRender();
    }).catch(fail);
    return () => {
      disposed = true; removePostRender?.();
      transport.disconnect(); document.removeEventListener('securitypolicyviolation', blockedResource);
      if (textureUrl) URL.revokeObjectURL(textureUrl);
      if (!globeViewer.isDestroyed()) globeViewer.destroy();
      viewer.current = null; imagery.current = null;
    };
  }, [attempt]);

  const toggle = () => {
    const next = !visible; setVisible(next);
    if (imagery.current) imagery.current.show = next;
    viewer.current?.scene.requestRender();
  };
  const reset = () => {
    const sphere = new Ellipsoid(RADIUS, RADIUS, RADIUS);
    viewer.current?.camera.setView({ destination: Cartesian3.fromDegrees(-70, 15, RADIUS * 2.1, sphere),
      orientation: { heading: 0, pitch: -CesiumMath.PI_OVER_TWO, roll: 0 } });
    viewer.current?.scene.requestRender();
  };
  const navigate = (action: 'rotate' | 'in' | 'out' | 'tilt') => {
    const current = viewer.current;
    if (!current) return;
    const camera = current.camera;
    if (action === 'rotate') camera.rotateRight(CesiumMath.toRadians(20));
    if (action === 'in') camera.zoomIn(Math.min(RADIUS * .3, Math.max(0, camera.positionCartographic.height - RADIUS * .02)));
    if (action === 'out') camera.zoomOut(Math.min(RADIUS * .3, Math.max(0, RADIUS * 6 - camera.positionCartographic.height)));
    if (action === 'tilt') camera.lookUp(CesiumMath.toRadians(8));
    current.scene.requestRender();
  };
  return <main>
    <div className="globe" ref={container} aria-label="Interactive ARCANA historical globe" />
    <header className="brand"><span className="brand-mark">A</span><div>ARCANA WORLD<span>HISTORICAL GLOBE / T0</span></div></header>
    <aside className="panel">
      <div className="eyebrow">{status === 'VERIFIED' ? selected === OLDEST ? 'RENDERED DATASET' : 'LAST RENDERED STATE' : 'EXPECTED T0 DATASET'}</div>
      <h1>210 <span>Ma</span></h1>
      <p className="intro">An authorial world at the beginning of its recorded history.</p>
      <div className="classification">SYNTHETIC_AUTHORIAL_INITIALIZATION</div>
      <div className="divider" />
      <label className="toggle"><span>Land &amp; ocean</span><input type="checkbox" checked={visible} onChange={toggle} disabled={status !== 'VERIFIED'} /></label>
      <div className="legend"><span><i className="land" />Land</span><span><i className="ocean" />Ocean</span><span><i className="coast" />Coastal cell</span></div>
      <p className="support">Original 1° cells · spherical surface<br />Topography is not rendered.</p>
      <div className={`verification ${status.toLowerCase()}`} role="status"><span className="status-dot" />{status === 'VERIFIED' ? 'VERIFIED LOCAL DATA' : status === 'LOADING' ? 'LOADING DATASET' : 'DATASET UNAVAILABLE'}</div>
      <p className="message" role={status === 'ERROR' ? 'alert' : undefined}>{message}</p>
      <div className="identity-label">DATASET IDENTITY</div><code title={EXPORT_ID}>{EXPORT_ID}</code>
      {status === 'ERROR' && <button onClick={() => { setVisible(true); setAttempt(n => n + 1); }}>Retry verified dataset</button>}
    </aside>
    <footer><span>Drag to rotate · Scroll to zoom · Ctrl-drag to tilt</span>
      <nav aria-label="Globe camera controls"><button aria-label="Rotate globe" onClick={() => navigate('rotate')}>↻</button>
        <button aria-label="Zoom in" onClick={() => navigate('in')}>+</button>
        <button aria-label="Zoom out" onClick={() => navigate('out')}>−</button>
        <button aria-label="Tilt view" onClick={() => navigate('tilt')}>↗</button>
        <button onClick={reset}>Reset view</button></nav></footer>
    <Timeline catalog={catalog} selected={selected} onSelect={setSelected}
      renderableIds={RENDERABLE_IDS}
      rendered={status === 'VERIFIED' ? catalog?.states[0] : undefined} />
  </main>;
}

createRoot(document.getElementById('root')!).render(<App />);
