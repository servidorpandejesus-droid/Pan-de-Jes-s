from django.contrib import admin

from .models import Category, Ingredient, InventoryMovement, Product, Production, ProductionItem, RecipeItem, Sale, SaleItem


admin.site.register(Category)
admin.site.register(Product)
admin.site.register(Ingredient)
admin.site.register(RecipeItem)
admin.site.register(Production)
admin.site.register(ProductionItem)
admin.site.register(Sale)
admin.site.register(SaleItem)
admin.site.register(InventoryMovement)
