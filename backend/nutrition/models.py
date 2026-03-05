from django.contrib.auth.models import User
from django.db import models


class UserProfile(models.Model):
    """Extended profile for NutriLogic users."""

    ACTIVITY_CHOICES = [
        ("sedentary", "Sedentary"),
        ("light", "Lightly Active"),
        ("moderate", "Moderately Active"),
        ("active", "Active"),
        ("very_active", "Very Active"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    activity_level = models.CharField(
        max_length=20, choices=ACTIVITY_CHOICES, default="moderate"
    )
    county = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile({self.user.username})"


class HealthCondition(models.Model):
    """Health conditions associated with a user profile."""

    profile = models.ForeignKey(
        UserProfile, on_delete=models.CASCADE, related_name="conditions"
    )
    condition = models.CharField(max_length=100)
    diagnosed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.profile.user.username} – {self.condition}"


class RecommendationLog(models.Model):
    """Persists each recommendation request and its Prolog-generated result."""

    profile = models.ForeignKey(
        UserProfile,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendation_logs",
    )
    symptoms = models.JSONField(default=list)
    condition = models.CharField(max_length=100, blank=True)
    recommendations = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Recommendation({self.pk}) – {self.condition or 'symptom-based'}"
