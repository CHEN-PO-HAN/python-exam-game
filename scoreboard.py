"""Utility helpers for loading and saving the local high-score board."""

import json
import os
from typing import List


def _ensure_directory(path: str) -> None:
    """Create parent directories when needed."""
    directory = os.path.dirname(os.path.abspath(path))
    if directory and not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)


def load_scores(path: str, limit: int) -> List[int]:
    """Read the scoreboard from disk, returning a descending list of scores."""
    if not os.path.isfile(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except (json.JSONDecodeError, OSError):
        return []
    if not isinstance(raw, list):
        return []
    filtered = [int(value) for value in raw if isinstance(value, (int, float))]
    filtered.sort(reverse=True)
    return filtered[:limit]


def save_scores(path: str, scores: List[int]) -> None:
    """Persist the scoreboard to disk."""
    _ensure_directory(path)
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(scores, handle)
    except OSError:
        pass


def record_score(scores: List[int], score: int, limit: int) -> List[int]:
    """Insert a new score into the in-memory list and keep it trimmed."""
    if score <= 0:
        return scores
    updated = list(scores)
    updated.append(int(score))
    updated.sort(reverse=True)
    return updated[:limit]
