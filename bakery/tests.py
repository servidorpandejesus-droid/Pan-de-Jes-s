from decimal import Decimal

from django.test import TestCase

from .models import Category, Ingredient, InventoryMovement, Product, Production, ProductionItem, RecipeItem, Sale, SaleItem


class BakeryInventoryTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Panadería")
        self.product = Product.objects.create(
            code="PAN-001",
            name="Pan francés",
            category=self.category,
            quantity_available=100,
            price=Decimal("8000"),
        )
        self.flour = Ingredient.objects.create(
            name="Harina",
            unit="kg",
            stock_quantity=Decimal("50"),
            minimum_stock=Decimal("10"),
        )
        self.yeast = Ingredient.objects.create(
            name="Levadura",
            unit="kg",
            stock_quantity=Decimal("10"),
            minimum_stock=Decimal("2"),
        )
        RecipeItem.objects.create(product=self.product, ingredient=self.flour, quantity_per_unit=Decimal("0.2"))
        RecipeItem.objects.create(product=self.product, ingredient=self.yeast, quantity_per_unit=Decimal("0.01"))

    def test_production_consumes_ingredients_and_updates_stock(self):
        production = Production.objects.create(production_date="2026-06-27", notes="Producción diaria")
        item = ProductionItem.objects.create(production=production, product=self.product, quantity=100)

        item.consume_ingredients()

        self.flour.refresh_from_db()
        self.yeast.refresh_from_db()
        self.product.refresh_from_db()
        self.assertEqual(self.flour.stock_quantity, Decimal("30"))
        self.assertEqual(self.yeast.stock_quantity, Decimal("9"))
        self.assertEqual(self.product.quantity_available, 200)
        self.assertEqual(InventoryMovement.objects.filter(movement_type="consumption").count(), 2)

    def test_sale_reduces_product_stock_and_records_movement(self):
        sale = Sale.objects.create(sale_date="2026-06-27", customer_name="Cliente diario")
        item = SaleItem.objects.create(sale=sale, product=self.product, quantity=3, unit_price=Decimal("8000"))

        item.apply_stock()

        self.product.refresh_from_db()
        self.assertEqual(self.product.quantity_available, 97)
        self.assertEqual(InventoryMovement.objects.filter(movement_type="sale").count(), 1)
        self.assertEqual(sale.total_amount, Decimal("24000"))
