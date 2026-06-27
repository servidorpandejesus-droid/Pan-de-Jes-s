from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404, redirect, render

from .models import Category, Ingredient, Product, Production, ProductionItem, Sale, SaleItem


def home(request):
    products = Product.objects.select_related("category").order_by("-created_at")[:5]
    ingredients = Ingredient.objects.order_by("name")
    low_stock = [ingredient for ingredient in ingredients if ingredient.is_low_stock]
    recent_sales = Sale.objects.order_by("-sale_date")[:5]
    recent_productions = Production.objects.order_by("-production_date")[:5]
    total_sales_amount = Sale.objects.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    best_selling = (
        SaleItem.objects.values("product__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")
        .first()
    )
    return render(
        request,
        "bakery/dashboard.html",
        {
            "products": products,
            "ingredients": ingredients,
            "low_stock": low_stock,
            "recent_sales": recent_sales,
            "recent_productions": recent_productions,
            "total_sales_amount": total_sales_amount,
            "best_selling": best_selling,
        },
    )


def products(request):
    if request.method == "POST":
        category, _ = Category.objects.get_or_create(name=request.POST.get("category_name", "General"))
        Product.objects.create(
            code=request.POST.get("code"),
            name=request.POST.get("name"),
            category=category,
            quantity_available=int(request.POST.get("quantity_available", 0)),
            price=Decimal(request.POST.get("price", "0")),
        )
        return redirect("bakery:products")

    products_list = Product.objects.select_related("category").order_by("name")
    categories = Category.objects.order_by("name")
    return render(request, "bakery/products.html", {"products": products_list, "categories": categories})


def ingredients(request):
    if request.method == "POST":
        Ingredient.objects.create(
            name=request.POST.get("name"),
            unit=request.POST.get("unit", "kg"),
            stock_quantity=Decimal(request.POST.get("stock_quantity", "0")),
            minimum_stock=Decimal(request.POST.get("minimum_stock", "0")),
            last_purchase_date=request.POST.get("last_purchase_date") or None,
        )
        return redirect("bakery:ingredients")

    ingredients_list = Ingredient.objects.order_by("name")
    return render(request, "bakery/ingredients.html", {"ingredients": ingredients_list})


@transaction.atomic
def productions(request):
    if request.method == "POST":
        production = Production.objects.create(
            production_date=request.POST.get("production_date"),
            notes=request.POST.get("notes", ""),
        )
        production_item = ProductionItem.objects.create(
            production=production,
            product=get_object_or_404(Product, pk=request.POST.get("product_id")),
            quantity=int(request.POST.get("quantity", 0)),
        )
        production_item.consume_ingredients()
        return redirect("bakery:productions")

    productions_list = Production.objects.order_by("-production_date")
    products = Product.objects.order_by("name")
    return render(request, "bakery/productions.html", {"productions": productions_list, "products": products})


@transaction.atomic
def sales(request):
    if request.method == "POST":
        sale = Sale.objects.create(
            sale_date=request.POST.get("sale_date"),
            customer_name=request.POST.get("customer_name", ""),
            notes=request.POST.get("notes", ""),
        )
        sale_item = SaleItem.objects.create(
            sale=sale,
            product=get_object_or_404(Product, pk=request.POST.get("product_id")),
            quantity=int(request.POST.get("quantity", 0)),
            unit_price=Decimal(request.POST.get("unit_price", "0")),
        )
        sale_item.apply_stock()
        return redirect("bakery:sales")

    sales_list = Sale.objects.order_by("-sale_date")
    products = Product.objects.order_by("name")
    return render(request, "bakery/sales.html", {"sales": sales_list, "products": products})


def reports(request):
    today = date.today()
    sales_daily = Sale.objects.filter(sale_date=today).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    sales_monthly = Sale.objects.filter(
        sale_date__year=today.year,
        sale_date__month=today.month,
    ).aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    production_history = (
        ProductionItem.objects
        .values("production__production_date")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-production__production_date")[:10]
    )
    best_sellers = (
        SaleItem.objects
        .values("product__name")
        .annotate(total_quantity=Sum("quantity"))
        .order_by("-total_quantity")[:5]
    )
    low_stock = [ingredient for ingredient in Ingredient.objects.order_by("name") if ingredient.is_low_stock]
    total_sales = Sale.objects.aggregate(total=Sum("total_amount"))["total"] or Decimal("0.00")
    return render(
        request,
        "bakery/reports.html",
        {
            "sales_daily": sales_daily,
            "sales_monthly": sales_monthly,
            "production_history": production_history,
            "best_sellers": best_sellers,
            "low_stock": low_stock,
            "total_sales": total_sales,
        },
    )
