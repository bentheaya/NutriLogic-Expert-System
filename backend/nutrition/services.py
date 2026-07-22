"""
Application services — orchestration between HTTP views, ORM, and inference.

Views should stay thin: validate input, call a service, return a Response.
"""

from __future__ import annotations

from typing import Any

from django.contrib.auth.models import User

from . import prolog_bridge
from .models import RecommendationLog, UserProfile
from .prolog_bridge import PrologInputError  # re-export for callers


def get_or_create_profile(user: User) -> UserProfile:
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def list_foods() -> list[dict]:
    """All foods from the knowledge base (process-cached)."""
    return list(prolog_bridge.get_foods())


def list_foods_by_group(group: str) -> list[dict]:
    return prolog_bridge.get_foods_by_group(group)


def food_micronutrients(food_name: str) -> dict | None:
    return prolog_bridge.get_micronutrients(food_name)


def recommend_by_condition(
    condition: str,
    *,
    user: User | None = None,
) -> dict[str, Any]:
    """
    Run condition-based meal recommendation and optionally persist a log.

    Returns ``{"condition": str, "recommendations": list}``.
    """
    recommendations = prolog_bridge.recommend_meal(condition)
    if user is not None and getattr(user, "is_authenticated", False):
        profile = get_or_create_profile(user)
        RecommendationLog.objects.create(
            profile=profile,
            condition=condition,
            recommendations=recommendations,
        )
    return {"condition": condition, "recommendations": recommendations}


def recommend_by_symptoms(
    symptoms: list[str],
    *,
    user: User | None = None,
) -> dict[str, Any]:
    """
    Run symptom-based recommendation and optionally persist a log.

    Returns ``{"symptoms": list, "recommendations": list}``.
    """
    recommendations = prolog_bridge.get_recommendation(symptoms)
    if user is not None and getattr(user, "is_authenticated", False):
        profile = get_or_create_profile(user)
        RecommendationLog.objects.create(
            profile=profile,
            symptoms=symptoms,
            recommendations=recommendations,
        )
    return {"symptoms": symptoms, "recommendations": recommendations}


def recommendation_history(user: User, *, limit: int = 20) -> list[RecommendationLog]:
    profile = getattr(user, "profile", None)
    if profile is None:
        return []
    return list(
        RecommendationLog.objects.filter(profile=profile)
        .order_by("-created_at")[:limit]
    )


def health_status() -> dict[str, Any]:
    """Lightweight readiness payload for ops probes."""
    from django.db import connection

    db_ok = False
    try:
        connection.ensure_connection()
        db_ok = True
    except Exception as exc:  # pragma: no cover – depends on runtime DB
        db_error = str(exc)
    else:
        db_error = None

    prolog_ok = False
    try:
        prolog_ok = prolog_bridge.is_available()
    except Exception:
        prolog_ok = False

    status = "ok" if db_ok and prolog_ok else "degraded"
    payload: dict[str, Any] = {
        "status": status,
        "database": "ok" if db_ok else "error",
        "prolog": "ok" if prolog_ok else "error",
    }
    if db_error:
        payload["database_detail"] = db_error
    return payload


__all__ = [
    "PrologInputError",
    "food_micronutrients",
    "get_or_create_profile",
    "health_status",
    "list_foods",
    "list_foods_by_group",
    "recommend_by_condition",
    "recommend_by_symptoms",
    "recommendation_history",
]
