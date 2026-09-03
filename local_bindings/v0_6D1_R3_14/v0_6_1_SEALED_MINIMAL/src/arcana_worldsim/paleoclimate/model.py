from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, Tuple
import math
import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter


CANONICAL_EVENTS = {
    "CHA_1": {
        "name": "Great Biotic Turnover",
        "analogue": "K-Pg-class impact extinction",
        "time_year_before_book": -66_000_000,
        "status": "CANONICAL_EVENT",
        "fixed_outcome": (
            "collapse of the dinosaur-grade dominant megafaunal ecological regime; "
            "surviving small-bodied clades, including mammal-like lineages, gain major "
            "post-extinction adaptive-radiation opportunity"
        ),
        "site_status": (
            "impact into a volatile-rich shallow-marine target is canonical; exact -66 Ma "
            "paleocoordinates remain provisional until the deep-time plate frame is interpolated"
        ),
    },
    "CHA_2": {
        "name": "Terminal Glacial Crisis",
        "analogue": "Younger-Dryas-like deglacial circulation crisis",
        "start_year_before_book": -14_000,
        "main_outburst_year_before_book": -12_900,
        "end_year_before_book": -12_000,
        "status": "CANONICAL_EVENT",
        "fixed_outcome": (
            "primitive cultures already exist; multiple regions experience causally related but "
            "non-identical megafloods, coastal transgression, extreme hydrological instability "
            "and abrupt climatic reversal, creating the substrate for later flood-myth families"
        ),
    },
}


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -50.0, 50.0)))


def _weighted_mean(field, mask, lat):
    w = np.cos(np.deg2rad(lat))[:, None]
    m = np.asarray(mask, dtype=bool)
    return float(np.sum(np.asarray(field, dtype=float) * w * m) / max(np.sum(w * m), 1e-12))


def _periodic_distance_cells_to_true(mask):
    mask = np.asarray(mask, dtype=bool)
    tiled = np.concatenate((mask, mask, mask), axis=1)
    d = distance_transform_edt(~tiled)
    nlon = mask.shape[1]
    return d[:, nlon:2*nlon]


def _orbital_forcing(time_years):
    """
    Earth-analogue Milankovitch proxy, intentionally not claimed as the final
    two-moon orbital solution. Positive values mean stronger summer ablation.

    The periods are physically motivated analogue periods. The phases are a
    candidate calibration producing a terminal deglaciation before CHA-2.
    """
    t = np.asarray(time_years, dtype=float)
    p23 = 9603.793806550066
    p41 = 553.7494246332965
    p100 = 5799.933923448708
    w23, w41, w100 = 0.21944756078334268, 0.4712668524115561, 0.30928558680510126
    precession = np.cos(2.0*np.pi*(t+p23)/23000.0)
    obliquity = np.cos(2.0*np.pi*(t+p41)/41000.0)
    eccentricity = np.cos(2.0*np.pi*(t+p100)/100000.0)
    summer = w23*precession + w41*obliquity + w100*eccentricity
    summer = (summer - np.mean(summer)) / max(float(np.std(summer)), 1e-12)
    return precession, obliquity, eccentricity, summer


def _simulate_recent_history(fire_susceptibility: float, seed: int = 617231) -> Dict[str, np.ndarray]:
    t = np.arange(-120_000.0, 0.1, 100.0)
    dt = 100.0
    n = t.size

    precession, obliquity, eccentricity, summer = _orbital_forcing(t)

    # Canonical CHA-2 freshwater forcing. This is a forcing pulse, not a
    # prescribed temperature response. The overturning model propagates it.
    freshwater_event_sv = (
        0.190*np.exp(-0.5*((t+12_900.0)/180.0)**2)
        + 0.045*np.exp(-0.5*((t+13_600.0)/350.0)**2)
    )

    # Background volcanic perturbations are causal/stochastic and reproducible,
    # not canonical historical anchors.
    rng = np.random.default_rng(seed)
    volcanic_aerosol_index = np.zeros(n, dtype=float)
    event = rng.random(n) < (dt/700.0)
    amp = rng.lognormal(mean=-2.8, sigma=0.7, size=n)
    volcanic_aerosol_index[event] = np.clip(amp[event], 0.0, 0.5)

    # Carbon reservoirs, GtC. Only net transfers are resolved. The active
    # lithospheric reservoir is intentionally enormous compared with the other
    # reservoirs, but all transfers close exactly at each time step.
    atm = np.zeros(n); ocean = np.zeros(n); biosphere = np.zeros(n); geo = np.zeros(n)
    atm[0] = 594.0              # ~280 ppm
    ocean[0] = 38_000.0
    biosphere[0] = 2_200.0
    geo[0] = 5_000_000.0

    temp = np.zeros(n)
    ice = np.zeros(n)
    overturning = np.ones(n)
    freshwater_sv = np.zeros(n)
    sea_level = np.zeros(n)

    flux_volcanic = np.zeros(n)
    flux_weathering = np.zeros(n)
    flux_airsea = np.zeros(n)
    flux_biosphere = np.zeros(n)
    flux_fire = np.zeros(n)

    ice[0] = 0.15

    for i in range(1, n):
        melt_rate = max(0.0, (ice[i-2] - ice[i-1]) / dt) if i > 1 else 0.0
        freshwater_sv[i] = freshwater_event_sv[i] + min(0.08, melt_rate*100.0)

        overturning_eq = np.clip(1.0 - 3.3*freshwater_sv[i], 0.25, 1.0)
        tau_m = 150.0 if overturning_eq < overturning[i-1] else 650.0
        overturning[i] = np.clip(
            overturning[i-1] + dt*(overturning_eq-overturning[i-1])/tau_m,
            0.20, 1.05,
        )

        ppm = max(atm[i-1] / 2.12, 80.0)
        f_co2 = 5.35*np.log(ppm/280.0)
        f_ice = -3.8*ice[i-1]
        f_orbit = 0.42*summer[i]
        f_overturning = -1.15*(1.0-overturning[i])
        f_aerosol = -4.0*volcanic_aerosol_index[i]
        t_eq = 0.85*(f_co2 + f_ice + f_orbit + f_overturning + f_aerosol)
        temp[i] = temp[i-1] + dt*(t_eq-temp[i-1])/650.0

        cold_index = -1.55*summer[i] - 0.50*temp[i] - 0.15
        ice_eq = 1.0/(1.0 + np.exp(-cold_index/0.50))
        tau_i = 6000.0 if ice_eq > ice[i-1] else 950.0
        ice[i] = np.clip(ice[i-1] + dt*(ice_eq-ice[i-1])/tau_i, 0.0, 1.0)

        # Net carbon fluxes, GtC/yr.
        flux_volcanic[i] = 0.080*(1.0 + 0.30*volcanic_aerosol_index[i])
        flux_weathering[i] = 0.080*(ppm/280.0)**0.32*np.exp(0.040*temp[i])

        # Warmer ocean and weakened overturning retain less carbon.
        atm_eq_ocean = 594.0 + 30.0*temp[i] + 10.0*(1.0-overturning[i])
        flux_airsea[i] = (atm[i-1] - atm_eq_ocean)/900.0

        atm_eq_bio = 594.0 + 6.0*temp[i]
        flux_biosphere[i] = (atm[i-1] - atm_eq_bio)/1000.0

        # Fire is a feedback, not an independent canonical event. Its global
        # strength is constrained by the v0.6 ecological fire susceptibility.
        flux_fire[i] = max(0.0, 0.008*(temp[i]+1.0)*(0.5+fire_susceptibility))

        d_airsea = flux_airsea[i]*dt
        d_bio = flux_biosphere[i]*dt
        d_geo_atm = (flux_volcanic[i]-flux_weathering[i])*dt
        d_fire = flux_fire[i]*dt

        atm[i] = atm[i-1] - d_airsea - d_bio + d_geo_atm + d_fire
        ocean[i] = ocean[i-1] + d_airsea
        biosphere[i] = biosphere[i-1] + d_bio - d_fire
        geo[i] = geo[i-1] - d_geo_atm

    # First-order eustatic relation for the analogue glacial cycle. Book-era
    # sea level is the zero datum; absolute ice volume is not being claimed.
    sea_level = -125.0*ice + 0.40*temp

    # Report anomalies relative to the exact book-era endpoint without changing
    # the dynamic state used inside the integration.
    temp_anomaly = temp - temp[-1]
    sea_level_anomaly = sea_level - sea_level[-1]

    total_carbon = atm + ocean + biosphere + geo

    return {
        "time_year_before_book": t,
        "precession_proxy": precession,
        "obliquity_proxy": obliquity,
        "eccentricity_proxy": eccentricity,
        "summer_ablation_forcing_index": summer,
        "atmospheric_carbon_gtc": atm,
        "ocean_carbon_gtc": ocean,
        "biosphere_soil_carbon_gtc": biosphere,
        "active_geologic_carbon_gtc": geo,
        "total_tracked_carbon_gtc": total_carbon,
        "atmospheric_co2_ppm": atm/2.12,
        "global_temperature_anomaly_c": temp_anomaly,
        "ice_volume_index": ice,
        "sea_level_anomaly_m": sea_level_anomaly,
        "overturning_strength": overturning,
        "freshwater_forcing_sv": freshwater_sv,
        "canonical_freshwater_pulse_sv": freshwater_event_sv,
        "volcanic_aerosol_index": volcanic_aerosol_index,
        "carbon_flux_volcanic_gtc_yr": flux_volcanic,
        "carbon_flux_weathering_gtc_yr": flux_weathering,
        "carbon_flux_airsea_gtc_yr": flux_airsea,
        "carbon_flux_biosphere_gtc_yr": flux_biosphere,
        "carbon_flux_fire_gtc_yr": flux_fire,
    }


def _trace_megaflood_sources(sh, hy) -> Tuple[np.ndarray, list]:
    lat = np.asarray(sh["lat"], dtype=float)
    lon = np.asarray(sh["lon"], dtype=float)
    owner = sh["owner_code"].astype(np.uint8)
    lake = hy["lake_candidate_mask"].astype(bool)
    depression = np.asarray(hy["depression_depth_m"], dtype=float)
    drainage = np.asarray(hy["drainage_area_km2"], dtype=float)
    receiver = np.asarray(hy["receiver_flat"], dtype=np.int64)
    nlat, nlon = owner.shape

    corridor = np.zeros((nlat, nlon), dtype=float)
    sources = []

    # Four independently selected proglacial-lake analogues in distinct plate/
    # continental systems. Selection is geophysical and deterministic.
    for oid in (1, 2, 3, 5):
        candidate = (
            lake
            & (owner == oid)
            & (np.abs(lat)[:, None] > 40.0)
            & (depression > 80.0)
        )
        score = np.where(
            candidate,
            depression*np.log1p(np.maximum(drainage, 0.0)),
            -1.0,
        )
        flat = int(np.argmax(score))
        if score.ravel()[flat] <= 0.0:
            continue
        si, sj = divmod(flat, nlon)
        path = []
        seen = set()
        cur = flat
        for _ in range(20_000):
            if cur < 0 or cur in seen:
                break
            seen.add(cur)
            path.append(cur)
            nxt = int(receiver[cur])
            if nxt < 0 or nxt == cur:
                break
            cur = nxt

        p_mask = np.zeros((nlat, nlon), dtype=float)
        if path:
            p_mask.ravel()[path] = 1.0
            # Corridor broadens downstream and represents valley-scale damage,
            # not literal water depth.
            p_mask = gaussian_filter(p_mask, sigma=(2.0, 2.0), mode=("reflect", "wrap"))
            p_mask /= max(float(np.max(p_mask)), 1e-12)
            corridor = np.maximum(corridor, p_mask)

        sources.append({
            "owner_code": int(oid),
            "latitude_deg": float(lat[si]),
            "longitude_deg": float(lon[sj]),
            "depression_depth_m": float(depression[si, sj]),
            "drainage_area_km2": float(drainage[si, sj]),
            "downstream_path_cell_count": int(len(path)),
        })

    return np.clip(corridor, 0.0, 1.0), sources


def _spatial_snapshots(root: Path, recent: Dict[str, np.ndarray]) -> Dict[str, Any]:
    inp = root / "inputs/v0_5_5I_SEALED"
    sh = np.load(inp / "shoreline_state_I.npz")
    cl = np.load(inp / "seasonal_climate_state_I.npz")
    hy = np.load(inp / "channel_hydrology_state_I.npz")
    eco = np.load(root / "inputs/v0_6_REFERENCE/ecology_state.npz")

    lat = np.asarray(sh["lat"], dtype=float)
    lon = np.asarray(sh["lon"], dtype=float)
    z = np.asarray(sh["elevation_m"], dtype=float)
    book_land = sh["effective_land_mask"].astype(bool)
    book_ocean = sh["ocean_mask"].astype(bool)
    owner = sh["owner_code"].astype(np.uint8)

    # Approximate distance from land to current ocean for circulation-regional
    # amplification. Geometry remains immutable.
    dcell = _periodic_distance_cells_to_true(book_ocean)
    dy_km = 111.195*0.25
    coslat = np.maximum(np.cos(np.deg2rad(lat))[:, None], 0.08)
    distance_ocean_km = dcell*dy_km*np.sqrt(coslat)
    ocean_influence = np.exp(-distance_ocean_km/900.0)

    lat2 = lat[:, None]
    abs_lat = np.abs(lat2)
    polar_amp = 1.0 + 0.55*(abs_lat/90.0)**1.5
    north_overturning_zone = _sigmoid((lat2-28.0)/6.0)*_sigmoid((79.0-lat2)/7.0)
    south_compensation_zone = _sigmoid((-lat2-32.0)/9.0)*_sigmoid((72.0+lat2)/8.0)

    years = np.array([-21_000.0, -14_000.0, -12_900.0, -12_000.0, 0.0])
    t = recent["time_year_before_book"]
    idx = np.array([int(np.argmin(np.abs(t-y))) for y in years], dtype=int)

    local_temp = np.zeros((years.size, lat.size, lon.size), dtype=np.float32)
    precip_factor = np.zeros_like(local_temp)
    npp_factor = np.zeros_like(local_temp)
    paleo_land = np.zeros((years.size, lat.size, lon.size), dtype=np.uint8)

    summer = recent["summer_ablation_forcing_index"]
    m = recent["overturning_strength"]
    global_t = recent["global_temperature_anomaly_c"]
    sea = recent["sea_level_anomaly_m"]

    for k, i in enumerate(idx):
        yd = np.clip((1.0-m[i])/0.65, 0.0, 1.25)
        circulation_anom = (
            -5.5*yd*north_overturning_zone*(0.35+0.65*ocean_influence)
            + 0.45*yd*south_compensation_zone
        )
        orbital_regional = 0.35*(summer[i]-summer[-1])*(abs_lat/90.0)**1.2
        dt_local = global_t[i]*polar_amp + circulation_anom + orbital_regional
        local_temp[k] = dt_local.astype(np.float32)

        pf = np.exp(0.035*dt_local)
        pf *= (1.0 - 0.27*yd*north_overturning_zone + 0.08*yd*south_compensation_zone)
        pf = np.clip(pf, 0.45, 1.45)
        precip_factor[k] = pf.astype(np.float32)

        nf = np.clip(np.exp(-np.abs(dt_local)/12.0)*(pf**0.45), 0.05, 1.35)
        npp_factor[k] = nf.astype(np.float32)
        paleo_land[k] = (z > sea[i]).astype(np.uint8)

    # CHA-2 transgression and megaflood exposure.
    i_start = int(np.argmin(np.abs(t+14_000.0)))
    i_peak = int(np.argmin(np.abs(t+12_900.0)))
    i_end = int(np.argmin(np.abs(t+12_000.0)))
    land_start = z > sea[i_start]
    land_end = z > sea[i_end]
    transgressed = land_start & (~land_end)

    trans_dist_cells = _periodic_distance_cells_to_true(transgressed)
    trans_dist_km = trans_dist_cells*dy_km*np.sqrt(coslat)
    transgression_exposure = np.exp(-trans_dist_km/80.0)
    transgression_exposure[~land_start] = 0.0

    megaflood_corridor, sources = _trace_megaflood_sources(sh, hy)
    floodplain = np.clip(np.asarray(hy["floodplain_width_km"], dtype=float)/12.0, 0.0, 1.0)
    q = np.asarray(hy["mean_discharge_m3_s"], dtype=float)
    qn = np.clip(np.log1p(q)/max(float(np.percentile(np.log1p(q[q>0]), 99.5)), 1e-9), 0.0, 1.0)
    lake = hy["lake_candidate_mask"].astype(bool)
    hydrologic = np.clip(0.55*floodplain + 0.30*qn + 0.15*lake.astype(float), 0.0, 1.0)

    flood_exposure = np.clip(
        0.50*megaflood_corridor
        + 0.36*transgression_exposure
        + 0.14*hydrologic,
        0.0, 1.0,
    )

    # Environmental support for future primitive-culture placement. This is
    # deliberately NOT a culture map and does not pre-write settlements.
    book_t = np.asarray(cl["annual_temperature_c"], dtype=float)
    npp = np.asarray(eco["npp_potential_g_m2_yr"], dtype=float)
    riparian = np.asarray(eco["riparian_potential"], dtype=float)
    hab_temp = _sigmoid((book_t+8.0)/4.0)*_sigmoid((32.0-book_t)/4.0)
    hab_npp = _sigmoid((npp-120.0)/140.0)
    water = np.clip(0.35 + 0.65*np.maximum(riparian, hydrologic), 0.0, 1.0)
    culture_habitat_potential = np.clip(hab_temp*hab_npp*water, 0.0, 1.0)
    culture_habitat_potential[~land_start] = 0.0

    flood_memory_potential = np.clip(
        flood_exposure*(0.45+0.55*culture_habitat_potential),
        0.0, 1.0,
    )

    return {
        "snapshot_year_before_book": years,
        "temperature_anomaly_c": local_temp,
        "precipitation_factor_relative_book": precip_factor,
        "npp_factor_relative_book": npp_factor,
        "paleo_land_mask": paleo_land,
        "cha2_transgressed_land_mask": transgressed.astype(np.uint8),
        "cha2_megaflood_corridor": megaflood_corridor.astype(np.float32),
        "cha2_flood_exposure": flood_exposure.astype(np.float32),
        "cha2_primitive_culture_habitat_potential": culture_habitat_potential.astype(np.float32),
        "cha2_flood_memory_potential": flood_memory_potential.astype(np.float32),
        "owner_code": owner,
        "megaflood_sources": sources,
        "cha2_sea_level_start_m": float(sea[i_start]),
        "cha2_sea_level_peak_m": float(sea[i_peak]),
        "cha2_sea_level_end_m": float(sea[i_end]),
        "cha2_sea_level_rise_m": float(sea[i_end]-sea[i_start]),
        "cha2_overturning_min": float(np.min(m[(t>=-14_000)&(t<=-12_000)])),
        "cha2_freshwater_peak_sv": float(np.max(recent["freshwater_forcing_sv"][(t>=-14_000)&(t<=-12_000)])),
    }


def _simulate_great_biotic_turnover() -> Dict[str, np.ndarray]:
    # Event-relative timeline: precise years for the impact winter and logarithmic
    # spacing for ecological/geochemical recovery.
    pre = np.array([-100.0, -10.0, -1.0, -0.1], dtype=float)
    post = np.concatenate(([0.0], np.logspace(-2.0, 6.0, 420)))
    t = np.unique(np.concatenate((pre, post)))
    pos = np.maximum(t, 0.0)
    active = t >= 0.0

    diameter_m = 12_000.0
    density = 3000.0
    velocity = 20_000.0
    mass = (4.0/3.0)*math.pi*(diameter_m/2.0)**3*density
    energy_j = 0.5*mass*velocity**2

    dust_tau = np.where(active, 2.8*np.exp(-pos/0.70), 0.0)
    sulfate_tau = np.where(active, 1.7*np.exp(-pos/2.50), 0.0)
    soot_tau = np.where(active, 1.3*np.exp(-pos/4.50), 0.0)
    optical_depth = dust_tau + sulfate_tau + soot_tau
    photosynthetically_active_radiation_fraction = np.exp(-optical_depth)

    preimpact_co2_ppm = 650.0
    carbon_pulse_gtc = 450.0
    atmospheric_excess_gtc = np.where(active, carbon_pulse_gtc*np.exp(-pos/120_000.0), 0.0)
    co2_ppm = preimpact_co2_ppm + atmospheric_excess_gtc/2.12
    greenhouse_forcing = 5.35*np.log(co2_ppm/preimpact_co2_ppm)

    impact_cooling = np.where(
        active,
        -16.0*(
            0.45*np.exp(-pos/0.60)
            + 0.35*np.exp(-pos/3.0)
            + 0.20*np.exp(-pos/10.0)
        ),
        0.0,
    )
    greenhouse_warming = 0.85*greenhouse_forcing*(1.0-np.exp(-pos/5.0))
    temperature_anomaly = impact_cooling + greenhouse_warming

    npp_multiplier = np.ones_like(t)
    npp_multiplier[active] = np.clip(
        photosynthetically_active_radiation_fraction[active]**0.55
        * np.exp(-np.maximum(0.0, -temperature_anomaly[active])/8.0),
        0.002, 1.0,
    )

    acidification_proxy = np.clip((co2_ppm-preimpact_co2_ppm)/250.0, 0.0, 1.0)
    extinction_pressure = np.zeros_like(t)
    extinction_pressure[active] = np.clip(
        0.66*(1.0-npp_multiplier[active])
        + 0.24*np.clip(np.abs(temperature_anomaly[active])/10.0, 0.0, 1.0)
        + 0.10*acidification_proxy[active],
        0.0, 1.0,
    )

    # Ecological opportunity is deliberately delayed: mass mortality is not the
    # same thing as adaptive radiation. The model only opens opportunity; it does
    # not prescribe which exact mammalian clade wins.
    opportunity = np.zeros_like(t)
    opportunity[active] = (
        (1.0-np.exp(-pos[active]/45_000.0))
        * np.exp(-np.maximum(0.0, extinction_pressure[active]-0.25)*1.5)
    )
    opportunity = np.clip(opportunity, 0.0, 1.0)

    # Deep-event carbon reservoirs. 450 GtC is instantaneously transferred from
    # biomass/volatile-rich target/geologic carbon into the atmosphere, then
    # redistributed. Total tracked carbon is analytically conserved.
    atm0 = preimpact_co2_ppm*2.12
    ocean0 = 40_000.0
    bio0 = 2_600.0
    geo0 = 5_500_000.0
    total0 = atm0+ocean0+bio0+geo0

    atm = np.full_like(t, atm0)
    bio = np.full_like(t, bio0)
    geo = np.full_like(t, geo0)
    atm[active] = atm0 + atmospheric_excess_gtc[active]
    # Initial source partition: 100 GtC biosphere, 350 GtC target/geologic.
    bio_loss = np.where(active, 100.0*np.exp(-pos/80_000.0), 0.0)
    geo_loss = np.where(active, 350.0*np.exp(-pos/180_000.0), 0.0)
    bio[active] = bio0 - bio_loss[active]
    geo[active] = geo0 - geo_loss[active]
    ocean = total0 - atm - bio - geo

    return {
        "event_time_year_before_book": np.float64(-66_000_000.0),
        "time_after_impact_year": t,
        "impactor_diameter_km": np.float64(diameter_m/1000.0),
        "impactor_velocity_km_s": np.float64(velocity/1000.0),
        "impactor_density_kg_m3": np.float64(density),
        "impact_energy_j": np.float64(energy_j),
        "dust_optical_depth": dust_tau,
        "sulfate_optical_depth": sulfate_tau,
        "soot_optical_depth": soot_tau,
        "total_optical_depth": optical_depth,
        "par_fraction": photosynthetically_active_radiation_fraction,
        "temperature_anomaly_c": temperature_anomaly,
        "preimpact_co2_ppm": np.float64(preimpact_co2_ppm),
        "atmospheric_co2_ppm": co2_ppm,
        "npp_multiplier": npp_multiplier,
        "extinction_pressure_index": extinction_pressure,
        "post_extinction_radiation_opportunity_index": opportunity,
        "atmospheric_carbon_gtc": atm,
        "ocean_carbon_gtc": ocean,
        "biosphere_carbon_gtc": bio,
        "active_geologic_carbon_gtc": geo,
        "total_tracked_carbon_gtc": atm+ocean+bio+geo,
    }


def build_paleoclimate_history(project_root, seed: int = 617231) -> Dict[str, Any]:
    root = Path(project_root)
    eco = np.load(root / "inputs/v0_6_REFERENCE/ecology_state.npz")
    sh = np.load(root / "inputs/v0_5_5I_SEALED/shoreline_state_I.npz")
    land = sh["effective_land_mask"].astype(bool)
    lat = np.asarray(sh["lat"], dtype=float)
    fire_susceptibility = _weighted_mean(
        np.asarray(eco["fire_disturbance_potential"], dtype=float), land, lat
    )

    recent = _simulate_recent_history(fire_susceptibility=fire_susceptibility, seed=seed)
    spatial = _spatial_snapshots(root, recent)
    impact = _simulate_great_biotic_turnover()

    # Non-canonical, causally generated recent volcanic-event catalogue.
    catalog = []
    v = recent["volcanic_aerosol_index"]
    t = recent["time_year_before_book"]
    for i in np.where(v >= 0.12)[0]:
        catalog.append({
            "type": "causal_background_volcanic_aerosol_pulse",
            "year_before_book": float(t[i]),
            "aerosol_index": float(v[i]),
            "canonical": False,
        })

    return {
        "canonical_events": CANONICAL_EVENTS,
        "recent": recent,
        "spatial": spatial,
        "great_biotic_turnover": impact,
        "background_event_catalog": catalog,
        "metadata": {
            "version": "0.6.1",
            "seed": int(seed),
            "book_era_reference": "v0.5.5I physical climate + v0.6 ecology",
            "physical_parent_mutated": False,
            "ecology_parent_mutated": False,
            "orbital_status": (
                "Earth-analogue Milankovitch periods and candidate phases; must be replaced or "
                "revalidated after the two-moon N-body/obliquity audit"
            ),
            "cha1_exact_impact_paleocoordinates": "PROVISIONAL_DEFERRED",
            "cha2_primitive_cultures": "CANONICAL_EXISTENCE_CONSTRAINT_ONLY; settlements not generated in v0.6.1",
        },
    }
