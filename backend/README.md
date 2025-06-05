### Step 1: Set Up Your Django Project

1. **Install Django and Django REST Framework**:
   ```bash
   pip install django djangorestframework
   ```

2. **Create a new Django project**:
   ```bash
   django-admin startproject foodgram
   cd foodgram
   ```

3. **Create a new Django app**:
   ```bash
   python manage.py startapp api
   ```

4. **Add the app and REST framework to your `settings.py`**:
   ```python
   INSTALLED_APPS = [
       ...
       'rest_framework',
       'api',
   ]
   ```

### Step 2: Define Your Models

In `api/models.py`, define the models for your application. For example, you might have models for `Recipe`, `Ingredient`, and `User`.

```python
from django.db import models
from django.contrib.auth.models import User

class Ingredient(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Recipe(models.Model):
    title = models.CharField(max_length=200)
    ingredients = models.ManyToManyField(Ingredient)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
```

### Step 3: Create Serializers

In `api/serializers.py`, create serializers for your models.

```python
from rest_framework import serializers
from .models import Recipe, Ingredient

class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = '__all__'

class RecipeSerializer(serializers.ModelSerializer):
    ingredients = IngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = '__all__'

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = Recipe.objects.create(**validated_data)
        for ingredient_data in ingredients_data:
            ingredient, created = Ingredient.objects.get_or_create(**ingredient_data)
            recipe.ingredients.add(ingredient)
        return recipe
```

### Step 4: Create Views

In `api/views.py`, create views for your API endpoints.

```python
from rest_framework import viewsets
from .models import Recipe, Ingredient
from .serializers import RecipeSerializer, IngredientSerializer

class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
```

### Step 5: Set Up Routing

In `api/urls.py`, set up the routing for your API.

```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RecipeViewSet, IngredientViewSet

router = DefaultRouter()
router.register(r'recipes', RecipeViewSet)
router.register(r'ingredients', IngredientViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

In your main `urls.py` file (`foodgram/urls.py`), include the API URLs.

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
```

### Step 6: Migrate the Database

Run the following commands to create the database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 7: Create a Superuser (Optional)

If you want to access the Django admin interface, create a superuser:

```bash
python manage.py createsuperuser
```

### Step 8: Run the Server

Finally, run your Django development server:

```bash
python manage.py runserver
```

### Step 9: Test Your API

You can test your API using tools like Postman or curl. The endpoints will be available at:

- `http://127.0.0.1:8000/api/recipes/`
- `http://127.0.0.1:8000/api/ingredients/`

### Conclusion

This is a basic setup for a Django REST API backend for the "Foodgram" web application. Depending on your project requirements, you may need to implement additional features such as authentication, permissions, filtering, pagination, and more. Make sure to refer to the Django REST Framework documentation for more advanced features and best practices.