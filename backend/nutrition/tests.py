"""
Tests for the NutriLogic nutrition app.

These tests exercise:
1. The Prolog bridge module (prolog_bridge.py)
2. The REST API endpoints

SWI-Prolog must be installed for Prolog bridge tests to pass.
If it is not available, those tests are skipped automatically.
"""

import importlib
import unittest
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


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
# Prolog Bridge tests
# ---------------------------------------------------------------------------

class PrologBridgeTests(TestCase):
    """Tests for nutrition.prolog_bridge using the real SWI-Prolog engine."""

    @skip_if_no_prolog
    def test_get_foods_returns_list(self):
        from nutrition import prolog_bridge
        foods = prolog_bridge.get_foods()
        self.assertIsInstance(foods, list)
        self.assertGreater(len(foods), 0)

    @skip_if_no_prolog
    def test_get_foods_have_expected_keys(self):
        from nutrition import prolog_bridge
        foods = prolog_bridge.get_foods()
        required_keys = {"name", "food_group", "calories_per_100g", "protein_g",
                         "carbs_g", "fat_g", "fibre_g"}
        for food in foods:
            self.assertTrue(required_keys.issubset(food.keys()),
                            f"Missing keys in: {food}")

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
        # Ugali and chapati should NOT appear as staples (avoid_for rule)
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


# ---------------------------------------------------------------------------
# API Endpoint tests (using mocked Prolog bridge)
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


class FoodListAPITests(APITestCase):
    """Tests for GET /api/foods/."""

    @patch("nutrition.views.prolog_bridge.get_foods", return_value=MOCK_FOODS)
    def test_food_list_returns_200(self, _mock):
        url = reverse("food-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("nutrition.views.prolog_bridge.get_foods", return_value=MOCK_FOODS)
    def test_food_list_returns_all_foods(self, _mock):
        url = reverse("food-list")
        response = self.client.get(url)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["name"], "ugali")


class FoodByGroupAPITests(APITestCase):
    """Tests for GET /api/foods/<group>/."""

    @patch(
        "nutrition.views.prolog_bridge.get_foods_by_group",
        return_value=[MOCK_FOODS[1]],
    )
    def test_food_by_group_returns_200(self, _mock):
        url = reverse("food-by-group", kwargs={"group": "vegetables"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch("nutrition.views.prolog_bridge.get_foods_by_group", return_value=[])
    def test_food_by_group_unknown_returns_404(self, _mock):
        url = reverse("food-by-group", kwargs={"group": "unknown_group"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class MicronutrientsAPITests(APITestCase):
    """Tests for GET /api/foods/<food_name>/micronutrients/."""

    @patch(
        "nutrition.views.prolog_bridge.get_micronutrients",
        return_value=MOCK_MICRONUTRIENTS,
    )
    def test_micronutrients_returns_200(self, _mock):
        url = reverse("food-micronutrients", kwargs={"food_name": "managu"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["iron_mg"], 3.0)

    @patch("nutrition.views.prolog_bridge.get_micronutrients", return_value=None)
    def test_micronutrients_missing_returns_404(self, _mock):
        url = reverse("food-micronutrients", kwargs={"food_name": "no_food"})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RecommendByConditionAPITests(APITestCase):
    """Tests for POST /api/recommend/condition/."""

    @patch(
        "nutrition.views.prolog_bridge.recommend_meal",
        return_value=MOCK_RECOMMENDATIONS,
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


class RecommendBySymptomsAPITests(APITestCase):
    """Tests for POST /api/recommend/symptoms/."""

    @patch(
        "nutrition.views.prolog_bridge.get_recommendation",
        return_value=MOCK_RECOMMENDATIONS,
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
