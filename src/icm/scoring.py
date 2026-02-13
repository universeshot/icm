from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol

from .models import Cog


def _letters_only(text: str) -> list[str]:
    return [char.lower() for char in text if char.isalpha()]


class FeatureTechnique(Protocol):
    id: str
    namespace: str
    feature_name: str

    def calculate(self, cog: Cog) -> float:
        ...


@dataclass
class CallableFeatureTechnique:
    id: str
    namespace: str
    feature_name: str
    calculator: Callable[[Cog], float]

    def calculate(self, cog: Cog) -> float:
        return float(self.calculator(cog))


@dataclass
class AlphabetPolarBreadthTechnique:
    id: str = "alpha_polar_breadth"
    namespace: str = "core"
    feature_name: str = "breadth"

    def calculate(self, cog: Cog) -> float:
        source = cog.content or cog.theme
        letters = _letters_only(source)
        if not letters:
            return 0.0
        min_value = min(ord(char) - ord("a") for char in letters)
        max_value = max(ord(char) - ord("a") for char in letters)
        return float(max_value - min_value)


@dataclass
class LetterDepthTechnique:
    id: str = "letter_depth"
    namespace: str = "core"
    feature_name: str = "depth"

    def calculate(self, cog: Cog) -> float:
        source = cog.content or cog.theme
        letters = _letters_only(source)
        if not letters:
            return 0.0
        counts: dict[str, int] = {}
        for char in letters:
            counts[char] = counts.get(char, 0) + 1
        return float(max(counts.values()))


@dataclass
class LetterVolumeTechnique:
    id: str = "letter_volume"
    namespace: str = "core"
    feature_name: str = "volume"

    def calculate(self, cog: Cog) -> float:
        source = cog.content or cog.theme
        letters = _letters_only(source)
        return float(len(letters))
