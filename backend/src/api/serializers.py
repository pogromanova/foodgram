import base64
import imghdr

from django.core.files.base import ContentFile
from django.db import transaction  
from rest_framework import serializers

from djoser.serializers import UserCreateSerializer, UserSerializer

from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag)
from users.models import Follow, User


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name=f'temp.{ext}')
        return super().to_internal_value(data)


class CustomUserCreateSerializer(UserCreateSerializer):    
    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'password')


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()
    avatar = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('email', 'id', 'username', 'first_name', 'last_name', 'is_subscribed', 'avatar')

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Follow.objects.filter(user=request.user, author=obj).exists()


class TagSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):    
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class RecipeIngredientSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='ingredient.id')
    name = serializers.ReadOnlyField(source='ingredient.name')
    measurement_unit = serializers.ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeSerializer(serializers.ModelSerializer):
    author = CustomUserSerializer(read_only=True)
    ingredients = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    
    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
    
    def get_image(self, obj):
        request = self.context.get('request')
        if obj.image and hasattr(obj.image, 'url'):
            return request.build_absolute_uri(obj.image.url) if request else obj.image.url
        return None
    
    def get_ingredients(self, obj):
        ingredients = []
        recipe_ingredients = RecipeIngredient.objects.filter(recipe=obj)
        for ri in recipe_ingredients:
            ingredients.append({
                'id': ri.ingredient.id,
                'name': ri.ingredient.name,
                'measurement_unit': ri.ingredient.measurement_unit,
                'amount': ri.amount
            })
        return ingredients
    
    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return Favorite.objects.filter(user=request.user, recipe=obj).exists()
    
    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if not request or request.user.is_anonymous:
            return False
        return ShoppingCart.objects.filter(user=request.user, recipe=obj).exists()


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(),
        required=True
    )
    image = Base64ImageField(required=True)  
    tags = serializers.PrimaryKeyRelatedField(
        queryset=Tag.objects.all(),
        many=True,
        required=False  
    )
    
    class Meta:
        model = Recipe
        fields = ('name', 'image', 'text', 'cooking_time', 'ingredients', 'tags')
    
    def validate(self, attrs):
        request = self.context.get('request')
        
        if request and request.method == 'POST':
            required_fields = ['name', 'text', 'cooking_time', 'image', 'ingredients']
            for field in required_fields:
                if field not in attrs:
                    raise serializers.ValidationError({field: 'Обязательное поле.'})
        
        return attrs
    
    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError('Нужен хотя бы один ингредиент!')
        
        ingredient_ids = []
        for item in value:
            if not isinstance(item, dict):
                raise serializers.ValidationError('Ингредиент должен быть объектом.')
            
            if 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError('Нужны поля id и amount!')
            
            try:
                ingredient_id = int(item['id'])
                ingredient_ids.append(ingredient_id)
            except:
                raise serializers.ValidationError('ID должен быть числом')
            
            try:
                amount = int(item['amount'])
                if amount < 1:
                    raise serializers.ValidationError('Количество должно быть больше 0!')
            except:
                raise serializers.ValidationError('Количество должно быть числом!')
        
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError('Ингредиенты повторяются!')
        
        existing_count = Ingredient.objects.filter(id__in=ingredient_ids).count()
        if existing_count != len(ingredient_ids):
            raise serializers.ValidationError('Некоторые ингредиенты не найдены!')
        
        return value
    
    def validate_name(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError('Название пустое.')
        if len(value) > 256:
            raise serializers.ValidationError('Название слишком длинное.')
        return value

    def validate_text(self, value):
        if not value or value.strip() == '':
            raise serializers.ValidationError('Описание пустое.')
        return value

    def validate_cooking_time(self, value):
        try:
            value = int(value)
            if value < 1:
                raise serializers.ValidationError('Время должно быть больше 0.')
        except:
            raise serializers.ValidationError('Время должно быть числом.')
        return value
    
    @transaction.atomic
    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        tags_data = validated_data.pop('tags', [])
        
        validated_data['author'] = self.context['request'].user
        
        recipe = Recipe.objects.create(**validated_data)
        
        if tags_data:
            recipe.tags.set(tags_data)
        
        for ingredient_data in ingredients_data:
            RecipeIngredient.objects.create(
                recipe=recipe,
                ingredient_id=ingredient_data['id'],
                amount=ingredient_data['amount']
            )
        
        return recipe
    
    @transaction.atomic
    def update(self, instance, validated_data):
        if 'ingredients' in validated_data:
            ingredients_data = validated_data.pop('ingredients')
            instance.recipe_ingredients.all().delete()
            for ingredient_data in ingredients_data:
                RecipeIngredient.objects.create(
                    recipe=instance,
                    ingredient_id=ingredient_data['id'],
                    amount=ingredient_data['amount']
                )
        
        if 'tags' in validated_data:
            tags = validated_data.pop('tags', [])
            instance.tags.set(tags)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

    def to_representation(self, instance):
        return RecipeSerializer(instance, context=self.context).data


class RecipeShortSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class AvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField(required=True)
    
    class Meta:
        model = User
        fields = ['avatar']
        
    def validate_avatar(self, value):
        if not value:
            raise serializers.ValidationError('Аватар обязателен.')
        
        if value.size > 2 * 1024 * 1024:
            raise serializers.ValidationError('Файл слишком большой.')
        
        image_format = imghdr.what(None, value.read())
        value.seek(0) 
        
        if not image_format:
            raise serializers.ValidationError('Неверный формат файла.')
            
        return value


class FollowSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source='author.id')
    username = serializers.ReadOnlyField(source='author.username')
    first_name = serializers.ReadOnlyField(source='author.first_name')
    last_name = serializers.ReadOnlyField(source='author.last_name')
    email = serializers.ReadOnlyField(source='author.email')
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()
    avatar = serializers.SerializerMethodField()
    
    class Meta:
        model = Follow
        fields = [
            'id', 'username', 'first_name', 'last_name',
            'email', 'is_subscribed', 'recipes', 'recipes_count', 'avatar'
        ]
        
    def get_is_subscribed(self, obj):
        return True  
        
    def get_recipes(self, obj):
        recipes_limit = self.context.get('recipes_limit')
        recipes = obj.author.recipes.all()
        if recipes_limit:
            try:
                recipes = recipes[:int(recipes_limit)]
            except:
                pass
        return RecipeShortSerializer(recipes, many=True, context=self.context).data
        
    def get_recipes_count(self, obj):
        return obj.author.recipes.count()
        
    def get_avatar(self, obj):
        if obj.author.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.author.avatar.url)
            return obj.author.avatar.url
        return None