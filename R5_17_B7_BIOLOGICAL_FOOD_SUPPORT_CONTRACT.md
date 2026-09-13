# R5.17-B7 - Natural Biological Food Support Contract

## Purpose

Materialize the natural/pre-management biological resource support available
to humans from already-authoritative ARCANA environment and biosphere state.

B7 is upstream of technology, managed resource systems, agriculture and
civilizational carrying capacity.

## Core separation

NATURAL BIOLOGICAL FOOD SUPPORT
        !=
HUMAN FOOD PRODUCTION
        !=
K(x,t)

B7 asks what biological food-resource opportunity exists in the simulated
natural world before human technology, processing, storage, management,
domestication or agriculture are applied.

## Candidate natural authorities

### A1 native forage vector

browse_forage
low_forage
wetland_forage
total_edible_forage

Authorized role:

native trophic / plant-resource substrate

Not authorized as:

physical biomass
human-edible calories
human carrying capacity

### R3.33 environmental resource state

Natural environmental components may be reused where their provenance is
independent of human readiness.

Human-conditioned readiness/contact fields must not enter the natural
baseline.

The R3.33 domestication-oriented candidate cohort must not be treated as an
exhaustive inventory of wild animal food resources.

### R3.34 pre-management producer landscape

Potentially useful pre-management fields include:

suitability
resource_abundance
harvest_return

harvest_return is a candidate refinement for human-accessible plant-resource
opportunity only where its temporal/domain semantics are valid.

propagation_opportunity is a management affordance and is excluded from the
natural B7 baseline unless separately justified.

Downstream producer coevolution/domestication outputs are excluded.

### H0 wild-animal state

B7 must inspect the complete relevant H0 fauna authority, guild structure,
spatial population/range state and trophic relationships.

A domestication-screening subset must not substitute for the natural fauna
resource layer.

### Aquatic / marine resources

Aquatic or marine support may be included only if an existing canonical
physical/biological authority is recovered.

If no adequate authority exists, the missing component remains an explicit
coverage gap. B7 must not invent marine productivity.

## Forbidden B7 inputs

R3.32 subsistence readiness
technology stocks
food processing
storage
landscape management
seasonal logistics
human-readiness-weighted contact opportunity
domestication trajectory
producer coevolution
agriculture
settlement
population target
city/state/polity target

## Initial component architecture

PLANT_TROPHIC_RESOURCE_SUPPORT
  source: A1/native ecological substrate

PLANT_HARVEST_OPPORTUNITY
  source: pre-management producer landscape where temporally valid

WILD_ANIMAL_RESOURCE_SUPPORT
  source: complete governed H0 fauna/ecology authority

AQUATIC_MARINE_RESOURCE_SUPPORT
  source: canonical authority if recovered
  otherwise: NOT_MATERIALIZED

Coverage masks, temporal domain, source identity and provenance must remain
attached to each component.

## Temporal guardrail

Authorities with different temporal domains must not be silently extended.

Deep-time A1 forage authority must not be confused with literal modern flora.
Recent producer models must not be backprojected into deep time as historical
species/resource states.

## B7-A1

First governed step:

SOURCE AUTHORITY + SCHEMA + COVERAGE PREFLIGHT

B7-A1 inventories actual materialized inputs and determines which natural
resource components can be bound without introducing a new biological model.

No scalar biological-food-support equation is authorized in B7-A1.

## B7 completion gate

NATURAL_PLANT_RESOURCE_SUPPORT: materialized_or_explicitly_bounded
NATURAL_WILD_ANIMAL_SUPPORT: materialized_or_explicitly_bounded
AQUATIC_MARINE_SUPPORT: materialized_or_explicitly_unavailable
HUMAN_MANAGEMENT_USED: false
POPULATION_TARGET_USED: false
K_X_T_MATERIALIZED: false
PROVENANCE_EXPLICIT: true
