from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _letters_only(text: str) -> list[str]:
    return [char.lower() for char in text if char.isalpha()]


@dataclass
class ShapeUniqueLettersTechnique:
    id: str = "shape_unique_letters"
    namespace: str = "shape"
    feature_name: str = "unique_letters"

    def calculate(self, cog: Any) -> float:
        source = cog.content or cog.theme
        letters = _letters_only(source)
        return float(len(set(letters)))


@dataclass
class ShapeVowelRatioTechnique:
    id: str = "shape_vowel_ratio"
    namespace: str = "shape"
    feature_name: str = "vowel_ratio"

    def calculate(self, cog: Any) -> float:
        source = cog.content or cog.theme
        letters = _letters_only(source)
        if not letters:
            return 0.0
        vowels = sum(1 for char in letters if char in {"a", "e", "i", "o", "u"})
        return float(vowels / len(letters))


def register_feature_techniques() -> list[object]:
    return [ShapeUniqueLettersTechnique(), ShapeVowelRatioTechnique()]
