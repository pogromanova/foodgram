import logging
import os
from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.conf import settings
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status, viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from users.models import Follow, User
from recipes.models import (
    Favorite, Ingredient, Recipe, RecipeIngredient, ShoppingCart, Tag
)
from .filters import IngredientFilter, RecipeFilter
from .pagination import LimitPageNumberPagination
from .permissions import IsAuthorOrReadOnly
from .serializers import (
    AvatarSerializer, CustomUserSerializer, FollowSerializer,
    IngredientSerializer, RecipeCreateSerializer, RecipeSerializer,
    RecipeShortSerializer, TagSerializer
)

logger = logging.getLogger(__name__)


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    pagination_class = None


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    pagination_class = None
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    
    def get_queryset(self):
        queryset = super().get_queryset()
        name_param = self.request.query_params.get('name')
        if name_param:
            queryset = queryset.filter(name__istartswith=name_param)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related('author').prefetch_related(
        'tags', 'ingredients', 'recipe_ingredients__ingredient'
    )
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = LimitPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def create(self, request, *args, **kwargs):
        ingredients_data = request.data.get('ingredients', [])
        if not ingredients_data:
            return Response(
                {'ingredients': ['Добавьте хотя бы один ингредиент']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Нет прав для редактирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        ingredients_data = request.data.get('ingredients', [])
        if not ingredients_data:
            return Response(
                {'ingredients': ['Добавьте хотя бы один ингредиент']},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Нет прав для редактирования'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if 'ingredients' in request.data:
            ingredients_data = request.data.get('ingredients', [])
            if not ingredients_data:
                return Response(
                    {'ingredients': ['Добавьте хотя бы один ингредиент']},
                    status=status.HTTP_400_BAD_REQUEST
                )
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        recipe = self.get_object()
        if recipe.author != request.user:
            return Response(
                {'detail': 'Нет прав для удаления'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            favorite_exists = Favorite.objects.filter(user=user, recipe=recipe).exists()
            if favorite_exists:
                return Response(
                    {'errors': 'Рецепт уже в избранном'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:  
            favorite_exists = Favorite.objects.filter(user=user, recipe=recipe).exists()
            if not favorite_exists:
                return Response(
                    {'errors': 'Рецепт не найден в избранном'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            Favorite.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        user = request.user
        
        if request.method == 'POST':
            cart_exists = ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
            if cart_exists:
                return Response(
                    {'errors': 'Рецепт уже в корзине'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:  
            cart_exists = ShoppingCart.objects.filter(user=user, recipe=recipe).exists()
            if not cart_exists:
                return Response(
                    {'errors': 'Рецепт не найден в корзине'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ShoppingCart.objects.filter(user=user, recipe=recipe).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        user = request.user
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=user
        ).select_related('ingredient').values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        
        if not ingredients.exists():
            return Response(
                {'detail': 'Корзина пуста'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shopping_list = []
        shopping_list.append("Список покупок:\n\n")
        
        for item in ingredients:
            line = f"• {item['ingredient__name']} - {item['total_amount']} {item['ingredient__measurement_unit']}\n"
            shopping_list.append(line)
            
        shopping_list.append("\nСоздано в Foodgram")
        
        response = HttpResponse(''.join(shopping_list), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = f"s/{recipe.id}"
        link = f'{request.build_absolute_uri("/")}{short_id}'
        return Response({'short-link': link}, status=status.HTTP_200_OK)


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    pagination_class = LimitPageNumberPagination
    permission_classes = [AllowAny]  
    
    def get_permissions(self):
        if self.action in ['me', 'set_password', 'avatar', 'subscribe', 'subscriptions']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @action(detail=False, methods=['get'])
    def me(self, request, *args, **kwargs):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post', 'delete'])
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        
        if user == author:
            return Response(
                {'errors': 'Нельзя подписаться на себя'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if request.method == 'POST':
            follow_exists = Follow.objects.filter(user=user, author=author).exists()
            if follow_exists:
                return Response(
                    {'errors': 'Уже подписаны'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            follow = Follow.objects.create(user=user, author=author)
            recipes_limit = request.query_params.get('recipes_limit')
            serializer = FollowSerializer(
                follow, 
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        else:  
            follow_exists = Follow.objects.filter(user=user, author=author).exists()
            if not follow_exists:
                return Response(
                    {'errors': 'Не подписаны на пользователя'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            Follow.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False)
    def subscriptions(self, request):
        user = request.user
        follows = Follow.objects.filter(user=user)
        recipes_limit = request.query_params.get('recipes_limit')
        
        pages = self.paginate_queryset(follows)
        serializer = FollowSerializer(
            pages, 
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)
    
    @action(detail=False, methods=['put', 'delete'], url_path='me/avatar')
    def avatar(self, request):
        user = request.user
        
        if request.method == 'PUT':
            if not request.data:
                return Response(
                    {'error': 'Нет данных аватара'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            if not os.path.exists(avatar_dir):
                os.makedirs(avatar_dir, exist_ok=True)
            
            serializer = AvatarSerializer(user, data=request.data)
            if serializer.is_valid():
                serializer.save()
                if user.avatar:
                    avatar_url = request.build_absolute_uri(user.avatar.url)
                else:
                    avatar_url = None
                return Response({'avatar': avatar_url})
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        elif request.method == 'DELETE':
            if user.avatar:
                user.avatar.delete()
                user.save()
            return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriptionListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user).order_by('id')
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        recipes_limit = self.request.query_params.get('recipes_limit')
        context['recipes_limit'] = recipes_limit
        return context