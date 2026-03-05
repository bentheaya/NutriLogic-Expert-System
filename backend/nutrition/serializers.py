from django.contrib.auth.models import User
from rest_framework import serializers

from .models import HealthCondition, RecommendationLog, UserProfile


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name"]
        read_only_fields = ["id"]


class HealthConditionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HealthCondition
        fields = ["id", "condition", "diagnosed_at"]
        read_only_fields = ["id", "diagnosed_at"]


class UserProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    conditions = HealthConditionSerializer(many=True, read_only=True)

    class Meta:
        model = UserProfile
        fields = [
            "id",
            "user",
            "age",
            "weight_kg",
            "height_cm",
            "activity_level",
            "county",
            "conditions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RecommendationLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecommendationLog
        fields = ["id", "symptoms", "condition", "recommendations", "created_at"]
        read_only_fields = ["id", "created_at"]


# ---------------------------------------------------------------------------
# Request / Response payloads (not tied to DB models)
# ---------------------------------------------------------------------------

class RecommendByConditionSerializer(serializers.Serializer):
    """Payload for /api/recommend/condition/ endpoint."""

    CONDITION_CHOICES = [
        "healthy",
        "hypertension",
        "type2_diabetes",
        "anaemia",
        "vitA_deficiency",
        "rickets",
        "unknown",
    ]

    condition = serializers.ChoiceField(choices=CONDITION_CHOICES)


class RecommendBySymptomsSerializer(serializers.Serializer):
    """Payload for /api/recommend/symptoms/ endpoint."""

    VALID_SYMPTOMS = [
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
    ]

    symptoms = serializers.ListField(
        child=serializers.ChoiceField(choices=VALID_SYMPTOMS),
        min_length=1,
    )
