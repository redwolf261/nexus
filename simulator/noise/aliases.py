"""
NEXUS Simulator — Name Alias Generator
Creates realistic alias variants for person names including:
  - English spelling variants (OCR errors, truncations)
  - Kannada script variants
  - Mixed code-switching variants
  - Police shorthand / abbreviations
  - Regional name variations
"""
from __future__ import annotations
import random
from typing import List, Optional


# Common OCR character confusions in police records
OCR_CONFUSIONS = {
    "a": ["o", "e", ""],
    "e": ["a", "i", ""],
    "i": ["l", "1", ""],
    "o": ["0", "a", ""],
    "n": ["m", "in", ""],
    "m": ["n", "nn", ""],
    "S": ["5", "s", ""],
    "I": ["l", "1", ""],
    "rn": ["m", "in", ""],
    "sh": ["s", ""],
    "th": ["t", ""],
}

# Common police record abbreviations
NAME_ABBREVIATIONS = {
    "Kumar": ["K.", "Kum.", "Kr."],
    "Shetty": ["S.", "Sht.", "Shty."],
    "Reddy": ["R.", "Rdy."],
    "Gowda": ["G.", "Gwd."],
    "Naik": ["N.", "Nk."],
    "Hegde": ["H.", "Hgd."],
    "Patil": ["P.", "Ptl."],
    "Singh": ["Sg.", "S."],
    "Sharma": ["Sh.", "Srm."],
    "Bhat": ["B.", "Bht."],
}

# Kannada to English transliteration variants (common inconsistencies)
TRANSLITERATION_VARIANTS = {
    "Rajesh":    ["Raajeesh", "Rajsh", "Raj", "Rajesh"],
    "Suresh":    ["Sureesh", "Sursh", "Sure", "Suresh"],
    "Ramesh":    ["Rameesh", "Ramsh", "Ram", "Ramesh"],
    "Mahesh":    ["Maheesh", "Mahsh", "Mahi", "Mahesh"],
    "Priya":     ["Priyah", "Pria", "Priya"],
    "Deepa":     ["Dipa", "Deepah", "Deepa"],
    "Kavitha":   ["Kavita", "Kawitha", "Kavitha"],
    "Shivakumar":["Shiva Kumar", "S. Kumar", "Shivakumara"],
    "Basavaraj": ["Basavaraja", "Bsavaraj", "Bsv Raj"],
    "Manjunath": ["Manjunatha", "M. Nath", "Manju"],
}


class AliasGenerator:
    """Generates realistic name aliases for entity resolution ground truth."""

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng

    def generate_aliases(
        self,
        canonical_name: str,
        canonical_name_kn: str,
        num_aliases: int = 3,
    ) -> List[str]:
        """
        Generate up to num_aliases alias variants for a name.
        Returns list of alias strings.
        """
        aliases = []
        parts = canonical_name.split()
        first_name = parts[0] if parts else canonical_name
        last_name = parts[-1] if len(parts) > 1 else ""

        generators = [
            self._abbreviate_last,
            self._ocr_corrupt,
            self._initial_first,
            self._drop_last,
            self._kannada_variant,
            self._transliteration_variant,
            self._police_shorthand,
            self._add_alias_prefix,
        ]

        self.rng.shuffle(generators)

        for gen in generators:
            if len(aliases) >= num_aliases:
                break
            alias = gen(canonical_name, canonical_name_kn, first_name, last_name)
            if alias and alias != canonical_name and alias not in aliases:
                aliases.append(alias)

        return aliases[:num_aliases]

    def _abbreviate_last(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        if last:
            return f"{first} {last[0]}."
        return None

    def _ocr_corrupt(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        name = list(first.lower())
        for i, ch in enumerate(name):
            if ch in OCR_CONFUSIONS and self.rng.random() < 0.3:
                replacement = self.rng.choice(OCR_CONFUSIONS[ch])
                name[i] = replacement
        corrupted = "".join(name).capitalize()
        return f"{corrupted} {last}".strip() if corrupted != first else None

    def _initial_first(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        if last:
            return f"{first[0]}. {last}"
        return None

    def _drop_last(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        if last:
            return first
        return None

    def _kannada_variant(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        if kn:
            return kn
        return None

    def _transliteration_variant(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        variants = TRANSLITERATION_VARIANTS.get(first)
        if variants:
            alt = self.rng.choice(variants)
            return f"{alt} {last}".strip() if last else alt
        return None

    def _police_shorthand(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        abbrevs = NAME_ABBREVIATIONS.get(last)
        if abbrevs:
            return f"{first} {self.rng.choice(abbrevs)}"
        return None

    def _add_alias_prefix(self, full: str, kn: str, first: str, last: str) -> Optional[str]:
        prefix = self.rng.choice(["@", "alias ", "a/k/a ", ""])
        if prefix:
            return f"{prefix}{first}"
        return None
