"""
Domain vocabulary — single source of truth for API validation.

These atoms MUST stay in sync with prolog/kb.pl.  Drift tests in tests.py
assert that every condition used by suitable_for/2 is listed here (and
vice-versa for the public recommendable set).
"""

# Conditions accepted by POST /api/recommend/condition/
# and produced by condition_for_deficiency/2 in the KB.
CONDITIONS = (
    "healthy",
    "hypertension",
    "type2_diabetes",
    "anaemia",
    "vitA_deficiency",
    "rickets",
    "unknown",
)

# Symptoms accepted by POST /api/recommend/symptoms/
SYMPTOMS = (
    "fatigue",
    "pale_skin",
    "night_blindness",
    "dry_skin",
    "frequent_infections",
    "bone_pain",
    "muscle_weakness",
    "rickets",
    "mouth_sores",
    "muscle_cramps",
)

# Food groups present in food/7 facts (for validation of path params).
FOOD_GROUPS = (
    "grains",
    "legumes_grains",
    "vegetables",
    "legumes",
    "tubers",
    "dairy",
    "fish",
    "meat",
    "protein",
    "nuts",
    "fruits",
)

# Activity levels for UserProfile (mirrored in the model choices).
ACTIVITY_LEVELS = (
    "sedentary",
    "light",
    "moderate",
    "active",
    "very_active",
)

# Strict Prolog atom pattern: lowercase letter then alphanumerics/underscores.
# Used to reject injection attempts before building query strings.
PROLOG_ATOM_RE = r"^[a-z][a-zA-Z0-9_]*$"

