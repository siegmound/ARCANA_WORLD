"""Path-independent semantic child seeds for the initial-world generator."""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256

import numpy as np


SEED_ROOT_MATERIAL = b"ARCANA:R6:INITIAL_WORLD:v1"
GENERATOR_VERSION = "ARCANA_R6_SUPERCONTINENT_GENERATOR_V1"
STREAM_NAMES = (
    "plate_mosaic",
    "continental_blocks",
    "coastline",
    "land_relief",
)


@dataclass(frozen=True, slots=True)
class SeedStream:
    name: str
    digest_sha256: str
    seed_uint128: int

    def rng(self) -> np.random.Generator:
        return np.random.Generator(np.random.PCG64(self.seed_uint128))

    def to_dict(self) -> dict[str, object]:
        return {"stream_name": self.name, "derivation_sha256": self.digest_sha256,
                "seed_uint128_hex": f"0x{self.seed_uint128:032x}",
                "bit_generator": "NumPy PCG64"}


def derive_seed_streams(names: tuple[str, ...] = STREAM_NAMES,
                        root_material: bytes = SEED_ROOT_MATERIAL) -> tuple[SeedStream, ...]:
    if len(names) != len(set(names)) or any(not n or "\\" in n or "/" in n for n in names):
        raise ValueError("seed stream names must be unique semantic identifiers")
    root_digest = sha256(root_material).digest()
    streams = []
    for name in names:
        digest = sha256(root_digest + b"\0" + GENERATOR_VERSION.encode("utf-8") +
                        b"\0" + name.encode("utf-8")).digest()
        streams.append(SeedStream(name, digest.hex(), int.from_bytes(digest[:16], "big")))
    return tuple(streams)


def lineage_manifest(root_material: bytes = SEED_ROOT_MATERIAL) -> dict[str, object]:
    return {
        "strategy_id": "ARCANA_R6_INITIAL_WORLD_SEED_LINEAGE_V1",
        "root_material_utf8": root_material.decode("utf-8"),
        "root_digest_sha256": sha256(root_material).hexdigest(),
        "generator_version": GENERATOR_VERSION,
        "child_derivation": "SHA256(root_digest_bytes || 0x00 || generator_version_utf8 || 0x00 || semantic_stream_name_utf8); first 128 bits unsigned big-endian",
        "streams": [s.to_dict() for s in derive_seed_streams(root_material=root_material)],
        "inheritance": "No HYBRID-1/R5 seed; adding a stream does not alter existing semantic stream seeds.",
    }
