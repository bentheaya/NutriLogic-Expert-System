from django.urls import path

from . import views

urlpatterns = [
    path("foods/", views.food_list, name="food-list"),
    path("foods/<str:group>/", views.food_by_group, name="food-by-group"),
    path(
        "foods/<str:food_name>/micronutrients/",
        views.food_micronutrients,
        name="food-micronutrients",
    ),
    path("recommend/condition/", views.recommend_by_condition, name="recommend-condition"),
    path("recommend/symptoms/", views.recommend_by_symptoms, name="recommend-symptoms"),
]
