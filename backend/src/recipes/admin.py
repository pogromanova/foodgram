from django.contrib import admin
from django.db.models import Count

from .models import (
    Ingredient,
    Recipe,
    RecipeComponent,
    UserFavorite,
    GroceryList,
)


class RecipeComponentInline(admin.TabularInline):
    model = RecipeComponent
    extra = 1
    min_num = 1
    autocomplete_fields = ("ingredient",)
    verbose_name = "Ингредиент"
    verbose_name_plural = "Ингредиенты в рецепте"


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "measurement_unit", "recipes_count")
    search_fields = ("name",)
    list_filter = ("measurement_unit",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(recipes_total=Count("used_in_recipes"))

    @admin.display(description="Кол-во рецептов")
    def recipes_count(self, obj):
        return obj.recipes_total


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "name",
        "author",
        "pub_date",
        "favorites_count",
    )
    list_filter = ("author", "pub_date")
    search_fields = (
        "name",
        "author__username",
        "author__email",
        "components__ingredient__name",
    )
    readonly_fields = ("pub_date", "favorites_count")
    inlines = (RecipeComponentInline,)
    autocomplete_fields = ("author",)
    date_hierarchy = "pub_date"
    ordering = ("-pub_date",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(fav_total=Count("in_favorites"))

    @admin.display(description="В избранном")
    def favorites_count(self, obj):
        return obj.fav_total

    actions = ["export_recipes_to_csv"]

    @admin.action(description="Экспортировать рецепты (+ ингредиенты) в CSV")
    def export_recipes_to_csv(self, request, queryset):
        import csv
        from django.http import HttpResponse

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=recipes.csv"
        writer = csv.writer(response)
        writer.writerow(
            ["id", "name", "author", "ingredient", "amount", "unit"])

        for recipe in queryset.prefetch_related("components__ingredient", "author"):
            for comp in recipe.components.all():
                writer.writerow(
                    [
                        recipe.id,
                        recipe.name,
                        recipe.author.get_full_name() or recipe.author.username,
                        comp.ingredient.name,
                        comp.amount,
                        comp.ingredient.measurement_unit,
                    ]
                )
        return response


@admin.register(UserFavorite)
class UserFavoriteAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "added_at")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    autocomplete_fields = ("user", "recipe")


@admin.register(GroceryList)
class GroceryListAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "recipe", "added_at")
    list_filter = ("user", "recipe")
    search_fields = ("user__username", "recipe__name")
    autocomplete_fields = ("user", "recipe")
