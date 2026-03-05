from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from . import prolog_bridge
from .serializers import (
    RecommendByConditionSerializer,
    RecommendBySymptomsSerializer,
)


@api_view(["GET"])
def food_list(request):
    """
    GET /api/foods/
    Return all Kenyan foods stored in the Prolog knowledge base.
    """
    foods = prolog_bridge.get_foods()
    return Response(foods)


@api_view(["GET"])
def food_by_group(request, group):
    """
    GET /api/foods/<group>/
    Return foods filtered by food group (e.g. vegetables, legumes, fish).
    """
    foods = prolog_bridge.get_foods_by_group(group)
    if not foods:
        return Response(
            {"detail": f"No foods found for group '{group}'."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(foods)


@api_view(["GET"])
def food_micronutrients(request, food_name):
    """
    GET /api/foods/<food_name>/micronutrients/
    Return micronutrient profile for a specific food.
    """
    data = prolog_bridge.get_micronutrients(food_name)
    if data is None:
        return Response(
            {"detail": f"Micronutrient data not found for '{food_name}'."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(data)


@api_view(["POST"])
def recommend_by_condition(request):
    """
    POST /api/recommend/condition/
    Body: {"condition": "hypertension"}

    Run the Prolog ``recommend_meal/3`` rule and return up to 5 meal options.
    """
    serializer = RecommendByConditionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    condition = serializer.validated_data["condition"]
    recommendations = prolog_bridge.recommend_meal(condition)
    return Response({"condition": condition, "recommendations": recommendations})


@api_view(["POST"])
def recommend_by_symptoms(request):
    """
    POST /api/recommend/symptoms/
    Body: {"symptoms": ["fatigue", "pale_skin"]}

    Diagnose deficiency from symptoms via Prolog backward chaining, then
    return personalised meal recommendations.
    """
    serializer = RecommendBySymptomsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    symptoms = serializer.validated_data["symptoms"]
    recommendations = prolog_bridge.get_recommendation(symptoms)
    return Response({"symptoms": symptoms, "recommendations": recommendations})
