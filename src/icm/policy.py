from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class PathPolicy:
    strategy_id: str
    score_set_id: str
    direction_mode: Literal["directed", "symmetrized"] = "directed"
    unseen_only: bool = True
    include_hidden_layers: bool = False
    selection_key: tuple[str, ...] = ("score_desc", "variance_asc", "stable_id_asc")
    equivalence_epsilon: float = 1e-9
    group_range: float | None = None
    min_score: float | None = None
    max_depth: int | None = None
    tags: set[str] = field(default_factory=set)
