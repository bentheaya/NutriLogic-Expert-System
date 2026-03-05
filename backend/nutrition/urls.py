from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

urlpatterns = [
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
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    # Profile & history (authenticated)
    path("profile/", views.profile, name="profile"),
    path("history/", views.recommendation_history, name="recommendation-history"),
]
