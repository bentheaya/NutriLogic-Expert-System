from django.contrib import admin

from .models import HealthCondition, RecommendationLog, UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ["user", "age", "weight_kg", "height_cm", "activity_level", "county"]
    search_fields = ["user__username", "county"]


@admin.register(HealthCondition)
class HealthConditionAdmin(admin.ModelAdmin):
    list_display = ["profile", "condition", "diagnosed_at"]
    list_filter = ["condition"]


@admin.register(RecommendationLog)
class RecommendationLogAdmin(admin.ModelAdmin):
    list_display = ["pk", "profile", "condition", "created_at"]
    list_filter = ["condition"]
    readonly_fields = ["created_at"]
