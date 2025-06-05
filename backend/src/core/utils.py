def create_shopping_list(ingredients):
    shopping_list = []
    for ingredient in ingredients:
        shopping_list.append(
            f"• {ingredient['ingredient__name']} "
            f"({ingredient['ingredient__measurement_unit']}) "
            f"— {ingredient['amount']}"
        )
    return shopping_list