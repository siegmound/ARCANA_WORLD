# VIEW-2T temporal catalog V1

`viewer/src/temporal.ts` defines the readonly `ARCANA_VIEW_TEMPORAL_CATALOG_V1`
contract. The current catalog is a detached, recursively frozen runtime snapshot
derived from the authenticated VIEW-1B manifest after the browser authenticates
both displayed numerical masks and verifies every decoded texture cell. It is
not a new scientific state, provider, HistoryStore or mutable catalog service.
No additional scientific data is generated or fetched by timeline navigation.

The sole registered export is
`viewexport_b0ff6b261de6640dce02256a94340b4c1d1f390e85914ddb48ada08493ba6df1`,
at 210 Ma. The original manifest SHA256 remains
`6b008eea5035a3749cb58de275a5c2f2f033dc62724c475ef72fb56f299b87f5`.
VIEW-2A source authentication and immutable staging remain the transport boundary.

Each entry retains its export identity, manifest digest, provenance inputs,
original geometry and selected layer records. Those records retain original
source/state identities, units, authority, validity/UNKNOWN rules, numerical file
identities and native spatial/temporal support. The catalog does not promote the
DISPLAY_ONLY imagery or replace source scientific authority. Branch is the export
baseline branch, not the viewer checkout's moving HEAD. History identity includes
the R6 initial-world baseline. Legacy R3/R5 and engineering experiments are not
registered or merged. Different resolutions can coexist as separate entries;
compatibility keys partition rendering support rather than silently resampling.

Historical time has a discriminated `HISTORICAL_BP` kind and integer years before
present in [0, 210000000]. Ma = 1000000 years, ka = 1000 years; 0 ka is the timeline
endpoint, not an asserted modern-world reconstruction. These presentation limits
are not continuous scientific coverage. Engineering elapsed time is a different
domain and is rejected by historical ordering. Sub-year resolution is unsupported
in V1. Labels preserve exact integer year selections even at geological scales.

Chronological order runs oldest to youngest: descending BP years, then ascending
export identity for same-time ties. Duplicate identities fail closed. Selection
is exact, in the explicit history/branch/compatibility scope, and requires VERIFIED
availability. INPUT_UNAVAILABLE, UNSUPPORTED and UNKNOWN entries never become
available checkpoints. Same-time ties use the stable identity order, never file
enumeration or ingestion order; this is presentation selection only. Future
catalog discovery must authenticate each manifest and separately qualify its
renderer before admission. This milestone does not implement generic discovery.

`interpolation=NONE`: gaps are implicitly UNKNOWN, with no invented endpoint,
nearest-state substitution, uniform time-step assumption or interpolation. State
checkpoint labels and event-ID lists are metadata extension points; the actual T0
event list is empty. Events do not create numerical support. Per-layer validity
continues to govern data within an available epoch.

Selected historical time and rendered dataset identity/time are independent.
At unsupported epochs the renderer retains T0, labels it **Last rendered state:
210 Ma**, and displays UNAVAILABLE for selection. It does not retime the imagery.
No catalog is advertised until authentication/rendering completes; errors clear
the catalog and report no rendered dataset. Camera and visibility remain VIEW-2A
operations and do not change the timeline or scientific data.

Previous/next selects the nearest strictly older/younger available checkpoint in
the explicit scope; nonexistent directions are disabled. At T0 both are disabled.
At an unsupported younger request, Previous can return to the existing T0; Next
remains disabled. Marker position uses actual age, not ordinal spacing. Native
range input supports pointer/touch scrubbing and keyboard Home/End/arrows.

Time-window zoom reduces/increases visible span by ten, down to one year, centered
on selection and bounded by the full domain. It changes navigation precision only.
Checkpoint navigation recenters a window when its target falls outside it. Full
history restores 210 Ma to 0 ka. The slider never extrapolates beyond this domain.

Playback controls require at least two distinct compatible VERIFIED epochs with
implemented renderers. Current renderer capability admits only the verified T0,
so Play is always disabled. The bounded controller is prepared to advance exact
checkpoints at one second of wall time per checkpoint and stop at the end; this
is not a geological evolution rate. Multi-dataset renderer dispatch and its browser
qualification require a separate scope before future datasets can enable playback.
