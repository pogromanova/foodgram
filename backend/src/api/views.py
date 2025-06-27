from django.db.models import Sum
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.shortcuts import redirect
from django.http import Http404
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet
from datetime import datetime
from io import BytesIO

from recipes.models import (Recipe, Ingredient,
                            RecipeComponent, UserFavorite,
                            GroceryList)
from users.models import User, Subscription
from .serializers import (
    UserSerializer, SubscriptionSerializer, AvatarSerializer,
    IngredientSerializer,

    RecipeReadSerializer, RecipeCreateSerializer,
    RecipeSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import CustomPagination
from .filters import IngredientFilter, RecipeFilter


def recipe_redirect(request, pk):

    try:
        recipe = Recipe.objects.get(id=pk)
        return redirect(f'/recipes/{pk}/')
    except Recipe.DoesNotExist:
        raise Http404("Рецепт не найден")


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    pagination_class = CustomPagination

    @action(detail=True, methods=['post', 'delete'], permission_classes=[IsAuthenticated])
    def subscribe(self, request, id=None):
        author = self.get_object()
        user = request.user
        if request.method == 'POST':
            if user == author:
                return Response(
                    {'errors': 'Нельзя подписаться на самого себя'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            subscription, created = Subscription.objects.get_or_create(
                user=user, author=author
            )
            if not created:
                return Response(
                    {'errors': f'Вы уже подписаны на пользователя {author.username}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            data = SubscriptionSerializer(
                author, context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        if Subscription.objects.filter(user=user, author=author).exists():
            Subscription.objects.filter(user=user, author=author).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': f'Вы не подписаны на пользователя {author.username}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=False, permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        user = request.user
        subscriptions = User.objects.filter(
            subscribers__user=user
        ).prefetch_related('authored_recipes', 'subscribers')

        page = self.paginate_queryset(subscriptions)
        serializer = SubscriptionSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(methods=['put', 'delete'], detail=False, url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def avatar(self, request):
        if request.method == 'PUT':
            serializer = AvatarSerializer(
                instance=request.user,
                data=request.data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        user = request.user
        if user.avatar:
            user.avatar.delete()
            user.avatar = None
            user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_permissions(self):
        if self.action == 'retrieve':
            self.permission_classes = [AllowAny]
        elif self.action in ['me', 'subscribe', 'subscriptions', 'avatar']:
            self.permission_classes = [IsAuthenticated]
        return super().get_permissions()


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = IngredientFilter
    permission_classes = (AllowAny,)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = (IsAuthorOrReadOnly,)
    pagination_class = CustomPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_queryset(self):
        return Recipe.objects.all().prefetch_related(
            'components__ingredient',
        ).select_related('author')

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return RecipeReadSerializer
        return RecipeCreateSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def handle_favorite_or_shopping_cart(self, request, pk, model_class):
        user = request.user
        recipe = get_object_or_404(Recipe, id=pk)
        verbose = model_class._meta.verbose_name

        if request.method == 'POST':
            obj, created = model_class.objects.get_or_create(
                user=user, recipe=recipe
            )
            if not created:
                return Response(
                    {'errors': f'Рецепт «{recipe.name}» уже в {verbose}!'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data = RecipeSerializer(recipe, context={'request': request}).data
            return Response(data, status=status.HTTP_201_CREATED)

        qs = model_class.objects.filter(user=user, recipe=recipe)
        if qs.exists():
            qs.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(
            {'errors': f'Рецепт не был добавлен в {verbose}'},
            status=status.HTTP_400_BAD_REQUEST
        )

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        return self.handle_favorite_or_shopping_cart(request, pk, UserFavorite)

    @action(detail=True,
            methods=['post', 'delete'],
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        return self.handle_favorite_or_shopping_cart(request, pk, GroceryList)

    @action(detail=False,
            permission_classes=[IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        user = request.user

        ingredients = RecipeComponent.objects.filter(
            recipe__in_grocery_lists__user=user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(amount=Sum('amount')).order_by('ingredient__name')

        recipes = Recipe.objects.filter(
            in_grocery_lists__user=user
        ).select_related('author')

        current_date = datetime.now().strftime('%d.%m.%Y')

        shopping_list = '\n'.join([
            f'Список покупок от {current_date}',
            '',
            'Продукты:',
            *[f'{i}. {item["ingredient__name"].capitalize()} '
              f'({item["ingredient__measurement_unit"]}) — {item["amount"]}'
              for i, item in enumerate(ingredients, 1)],
            '',
            'Рецепты:',
            *[f'• {recipe.name} (автор: {recipe.author.get_full_name() or recipe.author.username})'
              for recipe in recipes],
        ])

        response = FileResponse(
            BytesIO(shopping_list.encode('utf-8')),
            content_type='text/plain',
            filename='shopping_cart.txt'
        )
        return response

    @action(detail=True,
            methods=['get'],
            url_path='get-link')
    def get_link(self, request, pk=None):
        get_object_or_404(Recipe, id=pk)

        short_url = request.build_absolute_uri(
            reverse('recipe_redirect', args=[pk])
        )

        return Response({'short-link': short_url})
