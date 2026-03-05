"""
prolog_bridge.py
----------------
Bridge between the Django backend and the SWI-Prolog inference engine.

Uses the ``pyswip`` library to load ``prolog/kb.pl`` and expose helper
functions that the Django views can call directly.

Public API
~~~~~~~~~~
- ``get_foods()``                       → list of food dicts
- ``get_foods_by_group(group)``         → list of food dicts
- ``get_micronutrients(food_name)``     → dict or None
- ``recommend_meal(condition)``         → list of recommendation dicts
- ``get_recommendation(symptoms)``      → list of recommendation dicts
"""

import threading
from pathlib import Path
from typing import Any

from django.conf import settings

# ---------------------------------------------------------------------------
# Lazy initialisation – load the KB only once per process
# ---------------------------------------------------------------------------
_prolog = None
_lock = threading.Lock()


def _get_prolog():
    """Return a singleton :class:`pyswip.Prolog` instance with the KB loaded."""
    global _prolog
    if _prolog is not None:
        return _prolog

    with _lock:
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


def _meal_term_to_dict(meal_term, explanation: str) -> dict:
    """Convert a Prolog ``meal(Staple, Protein, Vegetable)`` functor to a dict."""
    # pyswip represents compound terms as Functor objects
    args = meal_term.args
    return {
        "staple": _atom(args[0]),
        "protein": _atom(args[1]),
        "vegetable": _atom(args[2]),
        "explanation": explanation,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def get_foods() -> list[dict]:
    """Return all foods from the Prolog knowledge base."""
    prolog = _get_prolog()
    query = "food(Name, Group, Cal, Prot, Carbs, Fat, Fibre)"
    return [_food_row_to_dict(row) for row in prolog.query(query)]


def get_foods_by_group(group: str) -> list[dict]:
    """Return foods belonging to a specific food group."""
    prolog = _get_prolog()
    query = f"food(Name, {group}, Cal, Prot, Carbs, Fat, Fibre)"
    return [_food_row_to_dict(row) for row in prolog.query(query)]


def get_micronutrients(food_name: str) -> dict | None:
    """Return micronutrient data for a specific food, or ``None`` if not found."""
    prolog = _get_prolog()
    query = (
        f"micronutrient({food_name}, Iron, Calcium, Zinc, VitA, VitC, Folate)"
    )
    results = list(prolog.query(query))
    if not results:
        return None
    row = results[0]
    row["Food"] = food_name
    return _micronutrient_row_to_dict(row)


def recommend_meal(condition: str) -> list[dict]:
    """
    Run the Prolog ``recommend_meal/3`` rule for the given health condition.

    Parameters
    ----------
    condition:
        A Prolog atom such as ``healthy``, ``hypertension``,
        ``type2_diabetes``, ``anaemia``, ``vitA_deficiency``, or ``rickets``.

    Returns
    -------
    list[dict]
        Up to 5 meal recommendations, each with keys
        ``staple``, ``protein``, ``vegetable``, and ``explanation``.
    """
    prolog = _get_prolog()
    query = f"recommend_meal({condition}, Meal, Explanation)"
    results = []
    for row in prolog.query(query):
        results.append(_meal_term_to_dict(row["Meal"], _atom(row["Explanation"])))
        if len(results) >= 5:
            break
    return results


def get_recommendation(symptoms: list[str]) -> list[dict]:
    """
    Diagnose deficiency from symptoms and return meal recommendations.

    Parameters
    ----------
    symptoms:
        A list of symptom strings, e.g. ``["fatigue", "pale_skin"]``.

    Returns
    -------
    list[dict]
        Up to 5 meal recommendations with keys
        ``staple``, ``protein``, ``vegetable``, and ``explanation``.
    """
    prolog = _get_prolog()
    # Build a Prolog list literal from the Python list
    prolog_list = "[" + ", ".join(symptoms) + "]"
    query = f"get_recommendation({prolog_list}, Meal, Explanation)"
    results = []
    for row in prolog.query(query):
        results.append(_meal_term_to_dict(row["Meal"], _atom(row["Explanation"])))
        if len(results) >= 5:
            break
    return results
