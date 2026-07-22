from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from django.urls import path
from rest_framework.permissions import AllowAny
from rest_framework.throttling import AnonRateThrottle
from rest_framework_simplejwt.views import TokenRefreshView

from . import views


class _RefreshThrottle(AnonRateThrottle):
    scope = "auth"


class AllowAnyTokenRefreshView(TokenRefreshView):
    """Refresh stays public even when DEFAULT_PERMISSION is IsAuthenticated."""

    permission_classes = [AllowAny]
    throttle_classes = [_RefreshThrottle]


class PublicSpectacularAPIView(SpectacularAPIView):
    permission_classes = [AllowAny]


class PublicSpectacularSwaggerView(SpectacularSwaggerView):
    permission_classes = [AllowAny]


class PublicSpectacularRedocView(SpectacularRedocView):
    permission_classes = [AllowAny]


urlpatterns = [
    # Ops & Documentation
    path("health/", views.health, name="health"),
    path("schema/", PublicSpectacularAPIView.as_view(), name="schema"),
    path("docs/", PublicSpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", PublicSpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # Food endpoints
    path("foods/", views.food_list, name="food-list"),
    path("foods/<str:group>/", views.food_by_group, name="food-by-group"),
    path(
        "foods/<str:food_name>/micronutrients/",
        views.food_micronutrients,
        name="food-micronutrients",
    ),
    # Recommendation endpoints
    path("recommend/condition/", views.recommend_by_condition, name="recommend-condition"),
    path("recommend/symptoms/", views.recommend_by_symptoms, name="recommend-symptoms"),
    # Authentication
    path("auth/register/", views.register, name="auth-register"),
    path("auth/token/", views.NutriLogicTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", AllowAnyTokenRefreshView.as_view(), name="token-refresh"),
    # Profile & history (authenticated)
    path("profile/", views.profile, name="profile"),
    path("history/", views.recommendation_history, name="recommendation-history"),
]
