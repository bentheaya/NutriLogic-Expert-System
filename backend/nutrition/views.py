from drf_spectacular.utils import OpenApiParameter, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework_simplejwt.views import TokenObtainPairView

from . import services
from .serializers import (
    NutriLogicTokenObtainPairSerializer,
    RecommendByConditionSerializer,
    RecommendBySymptomsSerializer,
    RecommendationLogSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class AuthRateThrottle(AnonRateThrottle):
    scope = "auth"


class RecommendRateThrottle(UserRateThrottle):
    scope = "recommend"


class NutriLogicTokenObtainPairView(TokenObtainPairView):
    """Login endpoint that embeds username in the access token."""

    permission_classes = [AllowAny]
    serializer_class = NutriLogicTokenObtainPairSerializer
    throttle_classes = [AuthRateThrottle]


_FoodItemListSerializer = inline_serializer(
    "FoodItemList",
    fields={
        "name": serializers.CharField(),
        "food_group": serializers.CharField(),
        "calories_per_100g": serializers.FloatField(),
        "protein_g": serializers.FloatField(),
        "carbs_g": serializers.FloatField(),
        "fat_g": serializers.FloatField(),
        "fibre_g": serializers.FloatField(),
    },
    many=True,
)

_MicronutrientSerializer = inline_serializer(
    "MicronutrientProfile",
    fields={
        "food": serializers.CharField(),
        "iron_mg": serializers.FloatField(),
        "calcium_mg": serializers.FloatField(),
        "zinc_mg": serializers.FloatField(),
        "vitA_ug": serializers.FloatField(),
        "vitC_mg": serializers.FloatField(),
        "folate_ug": serializers.FloatField(),
    },
)

_MealRecommendationSerializer = inline_serializer(
    "MealRecommendationList",
    fields={
        "staple": serializers.CharField(),
        "protein": serializers.CharField(),
        "vegetable": serializers.CharField(),
        "explanation": serializers.CharField(),
    },
    many=True,
)

_RecommendationResponseSerializer = inline_serializer(
    "RecommendationResponse",
    fields={
        "condition": serializers.CharField(required=False),
        "symptoms": serializers.ListField(child=serializers.CharField(), required=False),
        "deficiency": serializers.CharField(required=False),
        "recommendations": _MealRecommendationSerializer,
    },
)


@extend_schema(
    summary="Health Probe",
    description="Liveness and readiness check verifying Database and SWI-Prolog engine availability.",
    responses={
        200: inline_serializer(
            "HealthStatusOk",
            fields={
                "status": serializers.CharField(),
                "database": serializers.CharField(),
                "prolog": serializers.CharField(),
            },
        ),
        503: inline_serializer(
            "HealthStatusDegraded",
            fields={
                "status": serializers.CharField(),
                "database": serializers.CharField(),
                "prolog": serializers.CharField(),
            },
        ),
    },
    tags=["System"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def health(request):
    """
    GET /api/health/
    Liveness/readiness probe: database + Prolog engine.
    """
    payload = services.health_status()
    code = status.HTTP_200_OK if payload["status"] == "ok" else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(payload, status=code)


@extend_schema(
    operation_id="foods_list_all",
    summary="List Foods",
    description="Return all Kenyan foods stored in the SWI-Prolog knowledge base.",
    responses={200: _FoodItemListSerializer},
    tags=["Foods"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def food_list(request):
    """
    GET /api/foods/
    Return all Kenyan foods stored in the Prolog knowledge base.
    """
    foods = services.list_foods()
    return Response(foods)


@extend_schema(
    operation_id="foods_filter_by_group",
    summary="Filter Foods by Group",
    description="Return foods filtered by group (e.g., vegetables, legumes, fish).",
    responses={200: _FoodItemListSerializer},
    tags=["Foods"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def food_by_group(request, group):
    """
    GET /api/foods/<group>/
    Return foods filtered by food group (e.g. vegetables, legumes, fish).
    """
    try:
        foods = services.list_foods_by_group(group)
    except services.PrologInputError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if not foods:
        return Response(
            {"detail": f"No foods found for group '{group}'."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(foods)


@extend_schema(
    summary="Get Food Micronutrients",
    description="Return micronutrient breakdown (iron, calcium, vitA, vitC, etc.) for a specific food.",
    responses={200: _MicronutrientSerializer},
    tags=["Foods"],
)
@api_view(["GET"])
@permission_classes([AllowAny])
def food_micronutrients(request, food_name):
    """
    GET /api/foods/<food_name>/micronutrients/
    Return micronutrient profile for a specific food.
    """
    try:
        data = services.food_micronutrients(food_name)
    except services.PrologInputError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    if data is None:
        return Response(
            {"detail": f"Micronutrient data not found for '{food_name}'."},
            status=status.HTTP_404_NOT_FOUND,
        )
    return Response(data)


@extend_schema(
    summary="Recommend Meals by Condition",
    description="Run Prolog recommend_meal/3 rules for a given health condition (e.g., hypertension, type2_diabetes). Logs history if authenticated.",
    request=RecommendByConditionSerializer,
    responses={200: _RecommendationResponseSerializer},
    tags=["Recommendations"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecommendRateThrottle])
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
    try:
        payload = services.recommend_by_condition(condition, user=request.user)
    except services.PrologInputError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(payload)


@extend_schema(
    summary="Recommend Meals by Symptoms",
    description="Backward-chain Prolog rules to diagnose nutrient deficiencies from symptoms and return meal recommendations.",
    request=RecommendBySymptomsSerializer,
    responses={200: _RecommendationResponseSerializer},
    tags=["Recommendations"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([RecommendRateThrottle])
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
    try:
        payload = services.recommend_by_symptoms(symptoms, user=request.user)
    except services.PrologInputError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)

    return Response(payload)


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------

@extend_schema(
    summary="User Registration",
    description="Register a new user account and initialize a user profile.",
    request=UserRegistrationSerializer,
    responses={
        201: inline_serializer(
            "RegisterSuccessResponse",
            fields={"detail": serializers.CharField()},
        ),
    },
    tags=["Auth"],
)
@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([AuthRateThrottle])
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
    services.get_or_create_profile(user)
    return Response(
        {"detail": "Account created successfully. You can now log in."},
        status=status.HTTP_201_CREATED,
    )


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@extend_schema(
    summary="User Profile",
    description="Retrieve or partially update the authenticated user's profile.",
    request=UserProfileSerializer,
    responses={200: UserProfileSerializer},
    tags=["Profile"],
)
@api_view(["GET", "PATCH"])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    GET  /api/profile/  — return the authenticated user's profile.
    PATCH /api/profile/ — update age, weight_kg, height_cm, activity_level, county.
    """
    user_profile = services.get_or_create_profile(request.user)

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

@extend_schema(
    summary="Recommendation History",
    description="Retrieve the last 20 recommendation logs for the authenticated user.",
    responses={200: RecommendationLogSerializer(many=True)},
    tags=["History"],
)
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recommendation_history(request):
    """
    GET /api/history/
    Return the last 20 recommendation logs for the authenticated user.
    """
    logs = services.recommendation_history(request.user, limit=20)
    serializer = RecommendationLogSerializer(logs, many=True)
    return Response(serializer.data)
