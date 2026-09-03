"""ARCANA WorldSim governed arbitrary-age state query layer (R5+)."""

from .r50_query import (
    R50AuthorityError,
    R50QueryError,
    R50QueryContract,
    R50AuthorityResolver,
    execute_query,
    run_demonstration,
)

__all__ = [
    "R50AuthorityError",
    "R50QueryError",
    "R50QueryContract",
    "R50AuthorityResolver",
    "execute_query",
    "run_demonstration",
]
