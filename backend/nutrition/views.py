from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from . import prolog_bridge
from .models import RecommendationLog, UserProfile
from .serializers import (
    RecommendByConditionSerializer,
    RecommendBySymptomsSerializer,
    RecommendationLogSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
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
    If the request is authenticated, the result is saved to RecommendationLog.
    """
    serializer = RecommendByConditionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    condition = serializer.validated_data["condition"]
    recommendations = prolog_bridge.recommend_meal(condition)

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        RecommendationLog.objects.create(
            profile=profile,
            condition=condition,
            recommendations=recommendations,
        )

    return Response({"condition": condition, "recommendations": recommendations})


@api_view(["POST"])
def recommend_by_symptoms(request):
    """
    POST /api/recommend/symptoms/
    Body: {"symptoms": ["fatigue", "pale_skin"]}

    Diagnose deficiency from symptoms via Prolog backward chaining, then
    return personalised meal recommendations.
    If the request is authenticated, the result is saved to RecommendationLog.
    """
    serializer = RecommendBySymptomsSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    symptoms = serializer.validated_data["symptoms"]
    recommendations = prolog_bridge.get_recommendation(symptoms)

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        RecommendationLog.objects.create(
            profile=profile,
            symptoms=symptoms,
            recommendations=recommendations,
        )

    return Response({"symptoms": symptoms, "recommendations": recommendations})


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@api_view(["POST"])
def register(request):
    """
    POST /api/auth/register/
    Body: {"username": "...", "email": "...", "password": "...", "password2": "..."}
    Creates a new User and an empty UserProfile.
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = serializer.save()
    UserProfile.objects.get_or_create(user=user)
    return Response(
        {"detail": "Account created successfully. You can now log in."},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET  /api/profile/  — return the authenticated user's profile.
    PATCH /api/profile/ — update age, weight_kg, height_cm, activity_level, county.
    """
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "GET":
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)

    serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    serializer.save()
    return Response(serializer.data)


# ---------------------------------------------------------------------------
# Recommendation history
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendation_history(request):
    """
    GET /api/history/
    Return the last 20 recommendation logs for the authenticated user.
    """
    user_profile = getattr(request.user, "profile", None)
    if user_profile is None:
        return Response([])

    logs = RecommendationLog.objects.filter(profile=user_profile).order_by("-created_at")[:20]
    serializer = RecommendationLogSerializer(logs, many=True)
    return Response(serializer.data)
