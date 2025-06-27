from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    UserViewSet, IngredientViewSet, RecipeViewSet,
    recipe_redirect
)

router = DefaultRouter()
router.register('users', UserViewSet, basename='users')
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')

urlpatterns = [
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls)),
    path('recipes/<int:pk>/redirect/', recipe_redirect, name='recipe_redirect'),
]
