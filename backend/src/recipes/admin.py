from django.contrib import admin
from .models import Tag, Ingredient, Recipe, RecipeIngredient, Favorite, ShoppingCart


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    min_num = 1


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_unit')
    search_fields = ('name',)
    list_filter = ('measurement_unit',)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'author', 'pub_date', 'favorites_count')
    list_filter = ('author', 'tags', 'pub_date')
    search_fields = ('name', 'author__username', 'author__email')
    readonly_fields = ('pub_date', 'favorites_count')
    inlines = (RecipeIngredientInline,)
    filter_horizontal = ('tags',)
    
    def favorites_count(self, obj):
        return obj.favorited_by.count()
    favorites_count.short_description = 'В избранном'


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingCart)
class ShoppingCartAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'recipe')
    list_filter = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')