from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import (
    IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet,
    SubscriptionListView
)

router = DefaultRouter()
router.register('ingredients', IngredientViewSet, basename='ingredients')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('tags', TagViewSet, basename='tags')
router.register('users', UserViewSet, basename='users')

urlpatterns = [
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
    path('users/subscriptions/', SubscriptionListView.as_view(), name='subscriptions'),
]