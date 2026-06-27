from datetime import date
from decimal import Decimal

from django.db import models
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Product(models.Model):
    code = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    image_url = models.URLField(blank=True, default="", help_text="URL de imagen del producto")
    quantity_available = models.PositiveIntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.name}"


class Ingredient(models.Model):
    name = models.CharField(max_length=100, unique=True)
    unit = models.CharField(max_length=20, default="kg")
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    minimum_stock = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    last_purchase_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.name

    @property
    def is_low_stock(self):
        return self.stock_quantity <= self.minimum_stock


class RecipeItem(models.Model):
    product = models.ForeignKey(Product, related_name="recipe_items", on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, related_name="recipe_items", on_delete=models.CASCADE)
    quantity_per_unit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        unique_together = ("product", "ingredient")

    def __str__(self):
        return f"{self.product.name} -> {self.ingredient.name}"


class Production(models.Model):
    production_date = models.DateField(default=date.today)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Producción {self.production_date}"


class ProductionItem(models.Model):
    production = models.ForeignKey(Production, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="productions", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)

    def consume_ingredients(self):
        self.product.quantity_available += self.quantity
        self.product.save(update_fields=["quantity_available"])
        for recipe_item in self.product.recipe_items.all():
            consumed = recipe_item.quantity_per_unit * self.quantity
            ingredient = recipe_item.ingredient
            ingredient.stock_quantity -= consumed
            ingredient.save(update_fields=["stock_quantity"])
            InventoryMovement.objects.create(
                movement_type="consumption",
                product=self.product,
                ingredient=ingredient,
                quantity=consumed,
                notes=f"Consumo por producción de {self.quantity} unidades",
            )
        return True


class Sale(models.Model):
    sale_date = models.DateField(default=date.today)
    customer_name = models.CharField(max_length=100, blank=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Venta {self.id} - {self.sale_date}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name="sales", on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    @property
    def total_price(self):
        return self.unit_price * self.quantity

    def apply_stock(self):
        if self.product.quantity_available < self.quantity:
            raise ValueError("Stock insuficiente")
        self.product.quantity_available -= self.quantity
        self.product.save(update_fields=["quantity_available"])
        self.sale.total_amount += self.total_price
        self.sale.save(update_fields=["total_amount"])
        InventoryMovement.objects.create(
            movement_type="sale",
            product=self.product,
            quantity=self.quantity,
            notes=f"Venta de {self.quantity} unidades",
        )
        return True


class InventoryMovement(models.Model):
    MOVEMENT_TYPES = [
        ("consumption", "Consumo"),
        ("sale", "Venta"),
        ("adjustment", "Ajuste"),
    ]
    movement_type = models.CharField(max_length=20, choices=MOVEMENT_TYPES)
    product = models.ForeignKey(Product, related_name="movements", on_delete=models.CASCADE, null=True, blank=True)
    ingredient = models.ForeignKey(Ingredient, related_name="movements", on_delete=models.CASCADE, null=True, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.created_at}"
