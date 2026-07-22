from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .domain import CONDITIONS, SYMPTOMS
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


class UserRegistrationSerializer(serializers.Serializer):
    """Payload for POST /api/auth/register/."""

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField(required=False, default="")
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        try:
            validate_password(
                data["password"],
                user=User(
                    username=data.get("username", ""),
                    email=data.get("email", ""),
                ),
            )
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)}) from exc
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        return User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )


class NutriLogicTokenObtainPairSerializer(TokenObtainPairSerializer):
    """JWT pair that embeds ``username`` so the SPA can display identity."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["username"] = user.username
        return token


# ---------------------------------------------------------------------------
# Request / Response payloads (not tied to DB models)
# ---------------------------------------------------------------------------

class RecommendByConditionSerializer(serializers.Serializer):
    """Payload for /api/recommend/condition/ endpoint."""

    condition = serializers.ChoiceField(choices=CONDITIONS)


class RecommendBySymptomsSerializer(serializers.Serializer):
    """Payload for /api/recommend/symptoms/ endpoint."""

    symptoms = serializers.ListField(
        child=serializers.ChoiceField(choices=SYMPTOMS),
        min_length=1,
    )
