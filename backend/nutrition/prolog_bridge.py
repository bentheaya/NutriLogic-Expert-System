"""
prolog_bridge.py
----------------
Bridge between the Django backend and the SWI-Prolog inference engine.

Uses the ``pyswip`` library to load ``prolog/kb.pl`` and expose helper
functions that application services can call.

Public API
~~~~~~~~~~
- ``get_foods()``                       → list of food dicts
- ``get_foods_by_group(group)``         → list of food dicts
- ``get_micronutrients(food_name)``     → dict or None
- ``recommend_meal(condition)``         → list of recommendation dicts
- ``get_recommendation(symptoms)``      → list of recommendation dicts
- ``is_available()``                    → bool (engine + KB ready)
- ``clear_caches()``                    → reset food-list caches (tests)

Thread-safety
~~~~~~~~~~~~~
SWI-Prolog / pyswip is not thread-safe.  All queries are serialised with a
module-level lock.  Atom inputs are validated against a strict regex (and
domain whitelists where applicable) before interpolation into query strings.
"""

from __future__ import annotations

import re
import threading
from functools import lru_cache
from pathlib import Path
from typing import Any

from django.conf import settings

from .domain import CONDITIONS, FOOD_GROUPS, PROLOG_ATOM_RE, SYMPTOMS

# ---------------------------------------------------------------------------
# Lazy initialisation – load the KB only once per process
# ---------------------------------------------------------------------------
_prolog = None
_init_lock = threading.Lock()
# Serialises every query against the shared engine (init + query).
_query_lock = threading.Lock()

_ATOM_PATTERN = re.compile(PROLOG_ATOM_RE)


class PrologInputError(ValueError):
    """Raised when a value is not a safe Prolog atom / domain member."""


def _assert_atom(value: str, *, field: str = "value") -> str:
    """Validate *value* is a safe Prolog atom; return it unchanged."""
    if not isinstance(value, str) or not _ATOM_PATTERN.fullmatch(value):
        raise PrologInputError(
            f"Invalid {field}: must be a lowercase Prolog atom "
            f"(got {value!r})."
        )
    return value


def _assert_member(value: str, allowed: tuple[str, ...], *, field: str) -> str:
    _assert_atom(value, field=field)
    if value not in allowed:
        raise PrologInputError(f"Unknown {field}: {value!r}.")
    return value


def _get_prolog():
    """Return a singleton :class:`pyswip.Prolog` instance with the KB loaded."""
    global _prolog
    if _prolog is not None:
        return _prolog

    with _init_lock:
        if _prolog is not None:  # double-checked locking
            return _prolog

        from pyswip import Prolog  # noqa: PLC0415 – intentional lazy import

        prolog = Prolog()
        kb_path: Path = settings.PROLOG_KB_PATH
        if not kb_path.exists():
            raise FileNotFoundError(
                f"Prolog knowledge base not found at: {kb_path}. "
                "Ensure PROLOG_KB_PATH is configured correctly in settings.py."
            )
        prolog.consult(str(kb_path))
        _prolog = prolog

    return _prolog


def _query(query: str):
    """Run a Prolog query under the shared lock; return list of solution dicts."""
    prolog = _get_prolog()
    with _query_lock:
        return list(prolog.query(query))


def is_available() -> bool:
    """Return True if the Prolog engine can load the KB and answer a trivial query."""
    try:
        results = _query("food(ugali, Group, Cal, Prot, Carbs, Fat, Fibre)")
        return len(results) > 0
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _atom(value: Any) -> str:
    """Convert a pyswip Atom / Functor / plain value to a Python string."""
    return str(value)


def _food_row_to_dict(row: dict) -> dict:
    """Map a Prolog food/7 solution dict to a Python dict with labelled keys."""
    return {
        "name": _atom(row["Name"]),
        "food_group": _atom(row["Group"]),
        "calories_per_100g": float(row["Cal"]),
        "protein_g": float(row["Prot"]),
        "carbs_g": float(row["Carbs"]),
        "fat_g": float(row["Fat"]),
        "fibre_g": float(row["Fibre"]),
    }


def _micronutrient_row_to_dict(row: dict) -> dict:
    return {
        "food": _atom(row["Food"]),
        "iron_mg": float(row["Iron"]),
        "calcium_mg": float(row["Calcium"]),
        "zinc_mg": float(row["Zinc"]),
        "vitA_ug": float(row["VitA"]),
        "vitC_mg": float(row["VitC"]),
        "folate_ug": float(row["Folate"]),
    }


def _meal_term_to_dict(meal_term: Any, explanation: str) -> dict:
    """Convert a Prolog ``meal(Staple, Protein, Vegetable)`` functor or string representation to a dict."""
    if hasattr(meal_term, "args") and len(meal_term.args) >= 3:
        staple = _atom(meal_term.args[0])
        protein = _atom(meal_term.args[1])
        vegetable = _atom(meal_term.args[2])
    else:
        raw_str = str(meal_term).strip()
        match = re.match(
            r"^meal\(\s*([^,\s()]+)\s*,\s*([^,\s()]+)\s*,\s*([^,\s()]+)\s*\)$",
            raw_str,
        )
        if match:
            staple, protein, vegetable = match.groups()
            staple = _atom(staple)
            protein = _atom(protein)
            vegetable = _atom(vegetable)
        else:
            raise ValueError(f"Unexpected meal term format: {meal_term!r}")

    return {
        "staple": staple,
        "protein": protein,
        "vegetable": vegetable,
        "explanation": explanation,
    }


def _cap_meals(rows: list[dict], limit: int = 5) -> list[dict]:
    results = []
    for row in rows:
        results.append(_meal_term_to_dict(row["Meal"], _atom(row["Explanation"])))
        if len(results) >= limit:
            break
    return results


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def get_foods() -> tuple[dict, ...]:
    """Return all foods from the Prolog knowledge base (cached per process)."""
    query = "food(Name, Group, Cal, Prot, Carbs, Fat, Fibre)"
    return tuple(_food_row_to_dict(row) for row in _query(query))


def get_foods_by_group(group: str) -> list[dict]:
    """Return foods belonging to a specific food group."""
    group = _assert_member(group, FOOD_GROUPS, field="food group")
    # Prefer filtering the cached full list (same data, avoids extra engine hits).
    return [f for f in get_foods() if f["food_group"] == group]


def get_micronutrients(food_name: str) -> dict | None:
    """Return micronutrient data for a specific food, or ``None`` if not found."""
    food_name = _assert_atom(food_name, field="food name")
    # Only query foods that exist in the KB (whitelist via cached catalog).
    known = {f["name"] for f in get_foods()}
    if food_name not in known:
        return None
    query = (
        f"micronutrient({food_name}, Iron, Calcium, Zinc, VitA, VitC, Folate)"
    )
    results = _query(query)
    if not results:
        return None
    row = results[0]
    row["Food"] = food_name
    return _micronutrient_row_to_dict(row)


def recommend_meal(condition: str) -> list[dict]:
    """
    Run the Prolog ``recommend_meal/3`` rule for the given health condition.

    Returns up to 5 meal recommendations with keys
    ``staple``, ``protein``, ``vegetable``, and ``explanation``.
    """
    condition = _assert_member(condition, CONDITIONS, field="condition")
    query = f"recommend_meal({condition}, Meal, Explanation)"
    return _cap_meals(_query(query), limit=5)


def get_recommendation(symptoms: list[str]) -> list[dict]:
    """
    Diagnose deficiency from symptoms and return meal recommendations.

    Returns up to 5 meal recommendations with keys
    ``staple``, ``protein``, ``vegetable``, and ``explanation``.
    """
    if not symptoms:
        raise PrologInputError("symptoms list must not be empty.")
    safe = [_assert_member(s, SYMPTOMS, field="symptom") for s in symptoms]
    prolog_list = "[" + ", ".join(safe) + "]"
    query = f"get_recommendation({prolog_list}, Meal, Explanation)"
    return _cap_meals(_query(query), limit=5)


def clear_caches() -> None:
    """Clear process-local caches (used by tests)."""
    get_foods.cache_clear()
