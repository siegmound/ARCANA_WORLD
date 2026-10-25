/** VIEW-1A proposal. Presentation authority only; no scientific write API. */
export type Authority =
  | 'AUTHORIAL_SYNTHETIC_INITIALIZATION'
  | 'MODEL_DERIVED_FROM_CANONICAL_T0'
  | 'STOCHASTIC_CANONICAL_MODEL_REALIZATION'
  | 'NONCANONICAL_ENGINEERING'
  | 'NONE';

export type Availability = 'VERIFIED' | 'INPUT_UNAVAILABLE' | 'UNSUPPORTED';
export type CellValidity = 'VALID' | 'UNKNOWN' | 'UNSUPPORTED' | 'INVALID' | 'NOT_APPLICABLE';

export interface FileIdentity {
  readonly path: string;
  readonly sha256: string; // actual file bytes; semantic/state IDs are separate
  readonly bytes: number;
}

export interface LayerV1 {
  readonly id: string;
  readonly source: FileIdentity;
  readonly field: string;
  readonly stateId: string | null;
  readonly semanticIdentity: string | null;
  readonly availability: Availability;
  readonly authority: Authority;
  readonly sourceAuthority: string; // original label, never replaced by display authority
  readonly units: string; // explicit categorical/unitless is permitted; unknown is explicit
  readonly dtype: string;
  readonly shape: readonly number[];
  readonly spatial: {
    readonly kind: 'R6_GRID_CELL' | 'PARENT_CELL_FACE' | 'PARENT_CELL_EDGE' | 'PLATE_RECORD' | 'ENGINEERING_PROFILE';
    readonly support: string;
    readonly supportIds: readonly string[];
    readonly coordinateConvention: string;
  };
  readonly temporal: {
    readonly originMa: number;
    readonly elapsedYears: readonly number[]; // exact stored samples; never an interpolation license
    readonly interpolation: 'NONE';
  };
  readonly validity: {
    readonly supportRule: string;
    readonly unknownRule: string;
    readonly invalidRule: string;
    readonly notApplicableRule: string;
    readonly uncertaintyRule: string;
  };
  readonly numeric: FileIdentity | null; // raw, dtype-preserving numerical asset
  readonly imagery: FileIdentity | null; // disposable colorized derivative
}

export interface DatasetV1 {
  readonly schema: 'ARCANA_VIEW_EXPORT_DATASET_V1';
  readonly version: 1;
  readonly baseline: { readonly repository: string; readonly branch: string; readonly head: string };
  readonly geometry: {
    readonly type: 'SPHERE';
    readonly radiusM: 6371000;
    readonly shape: readonly [180, 360];
    readonly rowOrder: 'SOUTH_TO_NORTH';
    readonly columnOrder: 'WEST_TO_EAST';
    readonly periodicLongitude: true;
  };
  readonly layers: readonly LayerV1[];
  readonly scientificAuthorityPromoted: false;
}
