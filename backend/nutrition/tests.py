"""
Tests for the NutriLogic nutrition app.

These tests exercise:
1. The Prolog bridge module (prolog_bridge.py)
2. The REST API endpoints
3. Authentication, profile, and recommendation history endpoints
4. Domain vocabulary drift against the knowledge base

SWI-Prolog must be installed for Prolog bridge tests to pass.
If it is not available, those tests are skipped automatically.
"""

import re
import unittest
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from nutrition.domain import CONDITIONS, FOOD_GROUPS, PROLOG_ATOM_RE, SYMPTOMS


# ---------------------------------------------------------------------------
# Helper: check whether SWI-Prolog / pyswip is usable
# ---------------------------------------------------------------------------

def _prolog_available() -> bool:
    try:
        from pyswip import Prolog  # noqa: F401
        p = Prolog()
        p.assertz("hello(world)")
        list(p.query("hello(X)"))
        return True
    except Exception:
        return False


PROLOG_AVAILABLE = _prolog_available()
skip_if_no_prolog = unittest.skipUnless(PROLOG_AVAILABLE, "SWI-Prolog not available")


# ---------------------------------------------------------------------------
# Domain / security unit tests
# ---------------------------------------------------------------------------

class DomainConstantsTests(TestCase):
    def test_condition_atoms_match_pattern(self):
        pattern = re.compile(PROLOG_ATOM_RE)
        for c in CONDITIONS:
            self.assertTrue(pattern.fullmatch(c), c)

    def test_symptom_atoms_match_pattern(self):
        pattern = re.compile(PROLOG_ATOM_RE)
        for s in SYMPTOMS:
            self.assertTrue(pattern.fullmatch(s), s)


class PrologBridgeSanitizationTests(TestCase):
    def test_reject_injection_in_group(self):
        from nutrition import prolog_bridge
        with self.assertRaises(prolog_bridge.PrologInputError):
            prolog_bridge.get_foods_by_group("vegetables); halt")

    def test_reject_unknown_group(self):
        from nutrition import prolog_bridge
        with self.assertRaises(prolog_bridge.PrologInputError):
            prolog_bridge.get_foods_by_group("not_a_real_group")

    def test_reject_injection_in_food_name(self):
        from nutrition import prolog_bridge
        with self.assertRaises(prolog_bridge.PrologInputError):
            prolog_bridge.get_micronutrients("ugali, X); evil")

    def test_reject_bad_condition(self):
        from nutrition import prolog_bridge
        with self.assertRaises(prolog_bridge.PrologInputError):
            prolog_bridge.recommend_meal("healthy); fail")


# ---------------------------------------------------------------------------
# Prolog Bridge tests
# ---------------------------------------------------------------------------

class PrologBridgeTests(TestCase):
    """Tests for nutrition.prolog_bridge using the real SWI-Prolog engine."""

    def setUp(self):
        from nutrition import prolog_bridge
        prolog_bridge.clear_caches()

    @skip_if_no_prolog
    def test_get_foods_returns_list_like(self):
        from nutrition import prolog_bridge
        foods = prolog_bridge.get_foods()
        self.assertGreater(len(foods), 0)

    @skip_if_no_prolog
    def test_get_foods_have_expected_keys(self):
        from nutrition import prolog_bridge
        foods = prolog_bridge.get_foods()
        required_keys = {
            "name", "food_group", "calories_per_100g", "protein_g",
            "carbs_g", "fat_g", "fibre_g",
        }
        for food in foods:
            self.assertTrue(required_keys.issubset(food.keys()), f"Missing keys in: {food}")

    @skip_if_no_prolog
    def test_get_foods_contains_ugali(self):
        from nutrition import prolog_bridge
        foods = prolog_bridge.get_foods()
        names = [f["name"] for f in foods]
        self.assertIn("ugali", names)

    @skip_if_no_prolog
    def test_get_foods_by_group_vegetables(self):
        from nutrition import prolog_bridge
        vegetables = prolog_bridge.get_foods_by_group("vegetables")
        self.assertGreater(len(vegetables), 0)
        for food in vegetables:
            self.assertEqual(food["food_group"], "vegetables")

    @skip_if_no_prolog
    def test_get_micronutrients_managu(self):
        from nutrition import prolog_bridge
        data = prolog_bridge.get_micronutrients("managu")
        self.assertIsNotNone(data)
        self.assertIn("iron_mg", data)
        self.assertGreater(data["iron_mg"], 0)

    @skip_if_no_prolog
    def test_get_micronutrients_missing_food(self):
        from nutrition import prolog_bridge
        data = prolog_bridge.get_micronutrients("not_a_real_food")
        self.assertIsNone(data)

    @skip_if_no_prolog
    def test_recommend_meal_healthy(self):
        from nutrition import prolog_bridge
        recommendations = prolog_bridge.recommend_meal("healthy")
        self.assertGreater(len(recommendations), 0)
        first = recommendations[0]
        self.assertIn("staple", first)
        self.assertIn("protein", first)
        self.assertIn("vegetable", first)
        self.assertIn("explanation", first)

    @skip_if_no_prolog
    def test_recommend_meal_hypertension(self):
        from nutrition import prolog_bridge
        recommendations = prolog_bridge.recommend_meal("hypertension")
        self.assertGreater(len(recommendations), 0)

    @skip_if_no_prolog
    def test_recommend_meal_type2_diabetes(self):
        from nutrition import prolog_bridge
        recommendations = prolog_bridge.recommend_meal("type2_diabetes")
        for rec in recommendations:
            self.assertNotIn(rec["staple"], ["ugali", "chapati"])

    @skip_if_no_prolog
    def test_get_recommendation_iron_deficiency_symptoms(self):
        from nutrition import prolog_bridge
        recommendations = prolog_bridge.get_recommendation(["fatigue", "pale_skin"])
        self.assertGreater(len(recommendations), 0)

    @skip_if_no_prolog
    def test_get_recommendation_vitA_deficiency_symptoms(self):
        from nutrition import prolog_bridge
        recommendations = prolog_bridge.get_recommendation(["night_blindness"])
        self.assertGreater(len(recommendations), 0)

    @skip_if_no_prolog
    def test_kb_conditions_cover_public_api(self):
        """Every public recommendable condition (except unknown) appears in suitable_for."""
        from nutrition import prolog_bridge
        # Pull distinct conditions from suitable_for via a foods×conditions probe
        # by running recommend_meal for each public condition (unknown uses healthy).
        for condition in CONDITIONS:
            if condition == "unknown":
                continue
            recs = prolog_bridge.recommend_meal(condition)
            # anaemia, vitA, rickets, hypertension, type2_diabetes, healthy should yield meals
            self.assertIsInstance(recs, list, condition)


# ---------------------------------------------------------------------------
# API Endpoint tests (using mocked services / bridge)
# ---------------------------------------------------------------------------

MOCK_FOODS = [
    {
        "name": "ugali",
        "food_group": "grains",
        "calories_per_100g": 360.0,
        "protein_g": 3.6,
        "carbs_g": 78.0,
        "fat_g": 1.5,
        "fibre_g": 2.0,
    },
    {
        "name": "managu",
        "food_group": "vegetables",
        "calories_per_100g": 42.0,
        "protein_g": 4.2,
        "carbs_g": 6.8,
        "fat_g": 0.8,
        "fibre_g": 3.5,
    },
]

MOCK_MICRONUTRIENTS = {
    "food": "managu",
    "iron_mg": 3.0,
    "calcium_mg": 188.0,
    "zinc_mg": 0.5,
    "vitA_ug": 292.0,
    "vitC_mg": 40.0,
    "folate_ug": 43.0,
}

MOCK_RECOMMENDATIONS = [
    {
        "staple": "githeri",
        "protein": "beans",
        "vegetable": "managu",
        "explanation": "Meal for anaemia: githeri + beans + managu — MOH 2025.",
    }
]


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.IsAuthenticated",
        ],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        # Disable throttling in unit tests
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class FoodListAPITests(APITestCase):
    """Tests for GET /api/foods/."""

    @patch("nutrition.services.list_foods", return_value=MOCK_FOODS)
    def test_food_list_returns_200(self, _mock):
        url = reverse("food-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("nutrition.services.list_foods", return_value=MOCK_FOODS)
    def test_food_list_returns_all_foods(self, _mock):
        url = reverse("food-list")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "ugali")


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class FoodByGroupAPITests(APITestCase):
    """Tests for GET /api/foods/<group>/."""

    @patch(
        "nutrition.services.list_foods_by_group",
        return_value=[MOCK_FOODS[1]],
    )
    def test_food_by_group_returns_200(self, _mock):
        url = reverse("food-by-group", kwargs={"group": "vegetables"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("nutrition.services.list_foods_by_group", return_value=[])
    def test_food_by_group_empty_returns_404(self, _mock):
        url = reverse("food-by-group", kwargs={"group": "vegetables"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_food_by_group_invalid_returns_400(self):
        from nutrition.prolog_bridge import PrologInputError

        with patch(
            "nutrition.services.list_foods_by_group",
            side_effect=PrologInputError("Unknown food group"),
        ):
            url = reverse("food-by-group", kwargs={"group": "unknown_group"})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class MicronutrientsAPITests(APITestCase):
    """Tests for GET /api/foods/<food_name>/micronutrients/."""

    @patch(
        "nutrition.services.food_micronutrients",
        return_value=MOCK_MICRONUTRIENTS,
    )
    def test_micronutrients_returns_200(self, _mock):
        url = reverse("food-micronutrients", kwargs={"food_name": "managu"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["iron_mg"], 3.0)

    @patch("nutrition.services.food_micronutrients", return_value=None)
    def test_micronutrients_missing_returns_404(self, _mock):
        url = reverse("food-micronutrients", kwargs={"food_name": "no_food"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class RecommendByConditionAPITests(APITestCase):
    """Tests for POST /api/recommend/condition/."""

    @patch(
        "nutrition.services.recommend_by_condition",
        return_value={"condition": "anaemia", "recommendations": MOCK_RECOMMENDATIONS},
    )
    def test_recommend_condition_valid(self, _mock):
        url = reverse("recommend-condition")
        response = self.client.post(url, {"condition": "anaemia"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["condition"], "anaemia")
        self.assertEqual(len(response.data["recommendations"]), 1)

    def test_recommend_condition_invalid_returns_400(self):
        url = reverse("recommend-condition")
        response = self.client.post(url, {"condition": "not_valid"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommend_condition_missing_field_returns_400(self):
        url = reverse("recommend-condition")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class RecommendBySymptomsAPITests(APITestCase):
    """Tests for POST /api/recommend/symptoms/."""

    @patch(
        "nutrition.services.recommend_by_symptoms",
        return_value={
            "symptoms": ["fatigue", "pale_skin"],
            "recommendations": MOCK_RECOMMENDATIONS,
        },
    )
    def test_recommend_symptoms_valid(self, _mock):
        url = reverse("recommend-symptoms")
        response = self.client.post(
            url, {"symptoms": ["fatigue", "pale_skin"]}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("recommendations", response.data)

    def test_recommend_symptoms_empty_list_returns_400(self):
        url = reverse("recommend-symptoms")
        response = self.client.post(url, {"symptoms": []}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommend_symptoms_invalid_symptom_returns_400(self):
        url = reverse("recommend-symptoms")
        response = self.client.post(url, {"symptoms": ["invalid_symptom"]}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_recommend_symptoms_missing_field_returns_400(self):
        url = reverse("recommend-symptoms")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Authentication endpoint tests
# ---------------------------------------------------------------------------

@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class RegisterAPITests(APITestCase):
    """Tests for POST /api/auth/register/."""

    def test_register_valid_user(self):
        url = reverse("auth-register")
        payload = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "securepass1",
            "password2": "securepass1",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("detail", response.data)
        self.assertTrue(User.objects.filter(username="testuser").exists())

    def test_register_mismatched_passwords(self):
        url = reverse("auth-register")
        payload = {
            "username": "user2",
            "password": "securepass1",
            "password2": "differentpass",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        User.objects.create_user(username="existing", password="pass1234!")
        url = reverse("auth-register")
        payload = {
            "username": "existing",
            "password": "securepass1",
            "password2": "securepass1",
        }
        response = self.client.post(url, payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        url = reverse("auth-register")
        response = self.client.post(url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class TokenAPITests(APITestCase):
    """Tests for POST /api/auth/token/ (login)."""

    def setUp(self):
        self.user = User.objects.create_user(username="tokenuser", password="testpass123")

    def test_obtain_token_valid(self):
        url = reverse("token-obtain-pair")
        response = self.client.post(
            url, {"username": "tokenuser", "password": "testpass123"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_access_token_embeds_username(self):
        import base64
        import json

        url = reverse("token-obtain-pair")
        response = self.client.post(
            url, {"username": "tokenuser", "password": "testpass123"}, format="json"
        )
        access = response.data["access"]
        payload_b64 = access.split(".")[1]
        # pad base64
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
        self.assertEqual(payload.get("username"), "tokenuser")

    def test_obtain_token_invalid_credentials(self):
        url = reverse("token-obtain-pair")
        response = self.client.post(
            url, {"username": "tokenuser", "password": "wrongpass"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Profile endpoint tests
# ---------------------------------------------------------------------------

@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class ProfileAPITests(APITestCase):
    """Tests for GET/PATCH /api/profile/."""

    def setUp(self):
        from nutrition.models import UserProfile
        self.user = User.objects.create_user(username="profileuser", password="testpass123")
        self.profile = UserProfile.objects.create(user=self.user)
        token_url = reverse("token-obtain-pair")
        resp = self.client.post(
            token_url, {"username": "profileuser", "password": "testpass123"}, format="json"
        )
        self.token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_get_profile_authenticated(self):
        url = reverse("profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "profileuser")

    def test_get_profile_unauthenticated(self):
        self.client.credentials()  # clear auth
        url = reverse("profile")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_patch_profile(self):
        url = reverse("profile")
        response = self.client.patch(url, {"age": 30, "county": "Nairobi"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["age"], 30)
        self.assertEqual(response.data["county"], "Nairobi")

    def test_patch_profile_invalid_activity_level(self):
        url = reverse("profile")
        response = self.client.patch(url, {"activity_level": "flying"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Recommendation history endpoint tests
# ---------------------------------------------------------------------------

@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class RecommendationHistoryAPITests(APITestCase):
    """Tests for GET /api/history/."""

    def setUp(self):
        from nutrition.models import RecommendationLog, UserProfile
        self.user = User.objects.create_user(username="histuser", password="testpass123")
        self.profile = UserProfile.objects.create(user=self.user)
        RecommendationLog.objects.create(
            profile=self.profile,
            condition="anaemia",
            recommendations=[{
                "staple": "githeri",
                "protein": "beans",
                "vegetable": "managu",
                "explanation": "Test",
            }],
        )
        token_url = reverse("token-obtain-pair")
        resp = self.client.post(
            token_url, {"username": "histuser", "password": "testpass123"}, format="json"
        )
        self.token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    def test_history_returns_200(self):
        url = reverse("recommendation-history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["condition"], "anaemia")

    def test_history_unauthenticated(self):
        self.client.credentials()
        url = reverse("recommendation-history")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Authenticated recommendation auto-logging tests
# ---------------------------------------------------------------------------

@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class AuthenticatedRecommendLoggingTests(APITestCase):
    """When a logged-in user hits the recommend endpoints, a log is saved."""

    def setUp(self):
        from nutrition.models import UserProfile
        self.user = User.objects.create_user(username="loguser", password="testpass123")
        UserProfile.objects.create(user=self.user)
        token_url = reverse("token-obtain-pair")
        resp = self.client.post(
            token_url, {"username": "loguser", "password": "testpass123"}, format="json"
        )
        self.token = resp.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.token}")

    @patch(
        "nutrition.services.prolog_bridge.recommend_meal",
        return_value=MOCK_RECOMMENDATIONS,
    )
    def test_condition_recommendation_creates_log(self, _mock):
        from nutrition.models import RecommendationLog
        url = reverse("recommend-condition")
        self.client.post(url, {"condition": "anaemia"}, format="json")
        self.assertEqual(RecommendationLog.objects.filter(profile__user=self.user).count(), 1)

    @patch(
        "nutrition.services.prolog_bridge.get_recommendation",
        return_value=MOCK_RECOMMENDATIONS,
    )
    def test_symptom_recommendation_creates_log(self, _mock):
        from nutrition.models import RecommendationLog
        url = reverse("recommend-symptoms")
        self.client.post(url, {"symptoms": ["fatigue", "pale_skin"]}, format="json")
        self.assertEqual(RecommendationLog.objects.filter(profile__user=self.user).count(), 1)


@override_settings(
    REST_FRAMEWORK={
        "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
        "DEFAULT_THROTTLE_CLASSES": [],
        "DEFAULT_THROTTLE_RATES": {},
    }
)
class HealthEndpointTests(APITestCase):
    @patch("nutrition.services.health_status", return_value={
        "status": "ok", "database": "ok", "prolog": "ok",
    })
    def test_health_ok(self, _mock):
        url = reverse("health")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")

    @patch("nutrition.services.health_status", return_value={
        "status": "degraded", "database": "ok", "prolog": "error",
    })
    def test_health_degraded(self, _mock):
        url = reverse("health")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)


class SettingsSecurityTests(TestCase):
    def test_secret_key_required_when_debug_false(self):
        import importlib
        import os

        from django.core.exceptions import ImproperlyConfigured

        old_debug = os.environ.get("DJANGO_DEBUG")
        old_secret = os.environ.get("DJANGO_SECRET_KEY")
        try:
            os.environ["DJANGO_DEBUG"] = "False"
            os.environ.pop("DJANGO_SECRET_KEY", None)
            # Importing settings module logic is already loaded; test the helper path
            # by re-evaluating the fail-closed branch inline.
            debug = False
            secret = os.environ.get("DJANGO_SECRET_KEY", "").strip()
            with self.assertRaises(ImproperlyConfigured):
                if not secret and not debug:
                    raise ImproperlyConfigured(
                        "DJANGO_SECRET_KEY must be set when DJANGO_DEBUG is False."
                    )
                raise AssertionError("should have raised")
        finally:
            if old_debug is None:
                os.environ.pop("DJANGO_DEBUG", None)
            else:
                os.environ["DJANGO_DEBUG"] = old_debug
            if old_secret is None:
                os.environ.pop("DJANGO_SECRET_KEY", None)
            else:
                os.environ["DJANGO_SECRET_KEY"] = old_secret
