from django.shortcuts import get_object_or_404, redirect

from .models import Recipe


def recipe_redirect(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)
    return redirect(recipe.get_absolute_url())
