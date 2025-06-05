import logging
logger = logging.getLogger(__name__)

from django.http import HttpResponse
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from rest_framework.decorators import action, api_view, permission_classes  
from rest_framework.response import Response
from rest_framework import status
from recipes.models import RecipeIngredient, ShoppingCart

from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets, generics
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from djoser.views import UserViewSet as DjoserUserViewSet
from djoser.permissions import CurrentUserOrAdminOrReadOnly 
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
from django.conf import settings  


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
        name = self.request.query_params.get('name')
        if name:
            queryset = queryset.filter(name__istartswith=name)
        return queryset


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = LimitPageNumberPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateSerializer
        return RecipeSerializer
    
    
    def create(self, request, *args, **kwargs):
        try:
            ingredients = request.data.get('ingredients', [])
            if not ingredients:
                return Response(
                    {'ingredients': ['Нужен хотя бы один ингредиент!']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            logger.debug(f"Received recipe data: {request.data}")
            return super().create(request, *args, **kwargs)
        except Exception as e:
            logger.error(f"Recipe creation failed: {str(e)}")
            if 'JSON parse error' in str(e):
                return Response(
                    {'detail': 'Неверный формат JSON. Проверьте формат ингредиентов и их ID.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if hasattr(e, 'detail'):
                return Response({'detail': e.detail}, status=status.HTTP_400_BAD_REQUEST)
            
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    
    def check_author_permission(view_method):
        def wrapper(self, request, *args, **kwargs):
            recipe = self.get_object()
            if recipe.author != request.user:
                return Response(
                    {'detail': 'У вас недостаточно прав для выполнения данного действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_method(self, request, *args, **kwargs)
        return wrapper

    @check_author_permission
    def update(self, request, *args, **kwargs):
        try:
            recipe = self.get_object()
            
            if recipe.author != request.user:
                return Response(
                    {'detail': 'У вас недостаточно прав для выполнения данного действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            ingredients = request.data.get('ingredients', [])
            if not ingredients:
                return Response(
                    {'ingredients': ['Нужен хотя бы один ингредиент!']},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            return super().update(request, *args, **kwargs)
            
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Recipe update failed: {str(e)}")
            return Response(
                {'detail': 'Ошибка при обновлении рецепта'},
                status=status.HTTP_400_BAD_REQUEST 
            )
    def check_author_permission(view_method):
        def wrapper(self, request, *args, **kwargs):
            recipe = self.get_object()
            if recipe.author != request.user:
                return Response(
                    {'detail': 'У вас недостаточно прав для выполнения данного действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            return view_method(self, request, *args, **kwargs)
        return wrapper

    @check_author_permission
    def partial_update(self, request, *args, **kwargs):
        try:
            recipe = self.get_object()
            
            if recipe.author != request.user:
                return Response(
                    {'detail': 'У вас недостаточно прав для выполнения данного действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            if 'ingredients' in request.data:
                ingredients = request.data.get('ingredients', [])
                if not ingredients:
                    return Response(
                        {'ingredients': ['Нужен хотя бы один ингредиент!']},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            return super().partial_update(request, *args, **kwargs)
            
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            logger.error(f"Recipe partial update failed: {str(e)}")
            return Response(
                {'detail': 'Ошибка при обновлении рецепта'},
                status=status.HTTP_400_BAD_REQUEST  
            )

    def destroy(self, request, *args, **kwargs):
        try:
            recipe = self.get_object()
            
            if recipe.author != request.user:
                return Response(
                    {'detail': 'У вас недостаточно прав для выполнения данного действия.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            return super().destroy(request, *args, **kwargs)
            
        except Recipe.DoesNotExist:
            return Response(
                {'detail': 'Страница не найдена.'},
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
                return Response({'errors': 'Рецепт уже в избранном'}, status=status.HTTP_400_BAD_REQUEST)
            
            Favorite.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if not Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не найден в избранном'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Favorite.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        recipe = self.get_object()
        
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
                return Response(
                    {'errors': 'Рецепт уже в списке покупок'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            ShoppingCart.objects.create(user=request.user, recipe=recipe)
            serializer = RecipeShortSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if not ShoppingCart.objects.filter(user=request.user, recipe=recipe).exists():
            return Response(
                {'errors': 'Рецепт не найден в списке покупок'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        ShoppingCart.objects.filter(user=request.user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name', 'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        
        if not ingredients.exists():
            return Response(
                {'detail': 'В корзине нет товаров'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        shopping_list = ["Список покупок:\n\n"]
        for item in ingredients:
            shopping_list.append(
                f"• {item['ingredient__name']} - "
                f"{item['total_amount']} {item['ingredient__measurement_unit']}\n"
            )
        shopping_list.append("\nПриготовлено в Foodgram")
        
        response = HttpResponse(''.join(shopping_list), content_type='text/plain; charset=utf-8')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(detail=True, url_path='get-link')
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_id = f"s/{recipe.id}"
        return Response(
            {'short-link': f'{request.build_absolute_uri("/")}{short_id}'},
            status=status.HTTP_200_OK
        )


    





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
            if Follow.objects.filter(user=user, author=author).exists():
                return Response(
                    {'errors': 'Вы уже подписаны'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            follow = Follow.objects.create(user=user, author=author)
            recipes_limit = request.query_params.get('recipes_limit')
            serializer = FollowSerializer(
                follow, 
                context={'request': request, 'recipes_limit': recipes_limit}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        if not Follow.objects.filter(user=user, author=author).exists():
            return Response(
                {'errors': 'Вы не подписаны на этого пользователя'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        Follow.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    @action(detail=False)
    def subscriptions(self, request):
        user = request.user
        queryset = Follow.objects.filter(user=user)
        recipes_limit = request.query_params.get('recipes_limit')
        
        pages = self.paginate_queryset(queryset)
        serializer = FollowSerializer(
            pages, 
            many=True,
            context={'request': request, 'recipes_limit': recipes_limit}
        )
        return self.get_paginated_response(serializer.data)
    
    @action(
        detail=False,
        methods=['put', 'delete'],
        url_path='me/avatar'
    )
    def avatar(self, request):
        user = request.user
        
        if request.method == 'PUT':
            try:
                if not request.data:
                    return Response({'error': 'Отсутствует аватар'}, status=status.HTTP_400_BAD_REQUEST)
                
                import os
                avatar_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
                if not os.path.exists(avatar_dir):
                    try:
                        os.makedirs(avatar_dir, exist_ok=True)
                    except Exception as e:
                        logger.error(f"Cannot create avatar directory: {str(e)}")
                        return Response(
                            {'error': 'Системная ошибка при загрузке аватара'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR
                        )
                
                serializer = AvatarSerializer(user, data=request.data)
                if serializer.is_valid():
                    serializer.save()
                    # response_serializer = CustomUserSerializer(user, context={'request': request})
                    # return Response(response_serializer.data)
                    avatar_url = request.build_absolute_uri(user.avatar.url) if user.avatar else None
                    return Response({'avatar': avatar_url})
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
            except Exception as e:
                logger.error(f"Avatar update failed: {str(e)}")
                return Response(
                    {'error': 'Ошибка при обновлении аватара'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif request.method == 'DELETE':
            try:
                if user.avatar:
                    user.avatar.delete()
                    user.save()
                return Response(status=status.HTTP_204_NO_CONTENT)
            except Exception as e:
                logger.error(f"Avatar deletion failed: {str(e)}")
                return Response(
                    {'error': 'Ошибка при удалении аватара'},
                    status=status.HTTP_400_BAD_REQUEST
                )







class SubscriptionListView(generics.ListAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = LimitPageNumberPagination

    def get_queryset(self):
        return Follow.objects.filter(user=self.request.user).order_by('id')
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['recipes_limit'] = self.request.query_params.get('recipes_limit')
        return context