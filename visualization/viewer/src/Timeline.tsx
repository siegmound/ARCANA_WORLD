import { useEffect, useState } from 'react';
import { OLDEST, available, canPlay, checkpoints, formatTime, presentation, zoomWindow,
  type TemporalCatalog, type TemporalState } from './temporal';

export function Timeline({ catalog, selected, onSelect, rendered, renderableIds = [] }: {
  catalog?: TemporalCatalog; selected: number; onSelect: (years: number) => void; rendered?: TemporalState;
  renderableIds?: readonly string[];
}) {
  const [span, setSpan] = useState(OLDEST);
  const [anchor, setAnchor] = useState(OLDEST);
  const [playing, setPlaying] = useState(false);
  const window = zoomWindow(anchor, span);
  const scope = catalog?.states[0];
  const states = scope ? available(catalog!.states, scope) : [];
  const view = scope ? presentation(states, scope, selected, rendered) : undefined;
  const neighbors = scope ? checkpoints(states, scope, selected) : undefined;
  // Only states with an implemented, verified renderer can participate in playback.
  const playable = states.filter(s => renderableIds.includes(s.id));
  const playback = !!scope && canPlay(playable, scope);
  const resize = (size: number) => { setAnchor(selected); setSpan(size); };
  const choose = (years: number) => {
    setPlaying(false);
    if (years < window.younger || years > window.older) setAnchor(years);
    onSelect(years);
  };
  useEffect(() => {
    if (!playing) return;
    const next = scope && playback ? checkpoints(playable, scope, selected).next : undefined;
    if (!next) { setPlaying(false); return; }
    // One second of wall time per exact stored checkpoint; never a geological rate or interpolation.
    const timer = globalThis.setTimeout(() => { setAnchor(next.time.years); onSelect(next.time.years); }, 1000);
    return () => globalThis.clearTimeout(timer);
  }, [playing, playback, selected, catalog, rendered, onSelect, renderableIds]);
  return <section className="timeline" aria-label="Historical timeline"
    data-selected-years={selected} data-rendered-years={rendered?.time.years ?? 'NONE'}
    data-availability={view?.available ? 'AVAILABLE' : 'UNAVAILABLE'} data-interpolation="NONE">
    <div className="timeline-top"><div><div className="eyebrow">SELECTED TIME</div>
      <strong aria-label="Selected time">{formatTime(selected)}</strong></div>
      <div className="time-state" role="status">{view?.available ? 'Verified checkpoint available' : 'UNAVAILABLE · no verified dataset at selected time'}
        <span aria-label="Rendered dataset time">{rendered ? `${view?.retained ? 'Last rendered state' : 'Rendered dataset'}: ${formatTime(rendered.time.years)}` : 'No dataset rendered'}</span>
      </div><div className="time-actions">
        <button aria-label="Previous checkpoint" disabled={!neighbors?.previous} onClick={() => choose(neighbors!.previous!.time.years)}>←</button>
        <button aria-label="Play historical checkpoints" disabled={!playback} aria-pressed={playing}
          onClick={() => setPlaying(value => !value)} title="Playback requires multiple compatible verified datasets with implemented renderers">{playing ? 'Pause' : 'Play'}</button>
        <button aria-label="Next checkpoint" disabled={!neighbors?.next} onClick={() => choose(neighbors!.next!.time.years)}>→</button>
      </div></div>
    <div className="time-track"><input aria-label="Selected historical time" type="range" min={-window.older} max={-window.younger} step="1"
      value={-selected} aria-valuetext={formatTime(selected)} onChange={e => choose(-Number(e.target.value))} />
      <div className="checkpoint-markers">{states.filter(s => s.time.years <= window.older && s.time.years >= window.younger).map(s =>
        <button key={s.id} className="checkpoint" style={{ left: `${100 * (window.older - s.time.years) / (window.older - window.younger)}%` }}
          aria-label={`Select ${s.checkpoint.label} at ${formatTime(s.time.years)}`} title={`${s.checkpoint.label} · VERIFIED`} onClick={() => choose(s.time.years)}>◆</button>)}</div>
    </div>
    <div className="time-scale"><span>{formatTime(window.older)}</span><span>Historical years before present · gaps remain UNKNOWN</span><span>{formatTime(window.younger)}</span></div>
    <div className="time-bottom"><span>{states.length} verified globe checkpoint{states.length === 1 ? '' : 's'} · {playback ? 'Exact checkpoints only' : 'Playback requires 2 compatible renderable epochs'}</span>
      <div><button disabled={span <= 1} onClick={() => resize(Math.max(1, Math.floor(span / 10)))}>Zoom time in</button>
        <button disabled={span === OLDEST} onClick={() => resize(Math.min(OLDEST, span * 10))}>Zoom time out</button>
        <button onClick={() => resize(OLDEST)}>Full history</button></div></div>
  </section>;
}
