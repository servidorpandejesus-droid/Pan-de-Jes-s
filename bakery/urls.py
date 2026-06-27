from django.urls import path

from . import views

app_name = "bakery"

urlpatterns = [
    path("", views.home, name="home"),
    path("productos/", views.products, name="products"),
    path("insumos/", views.ingredients, name="ingredients"),
    path("produccion/", views.productions, name="productions"),
    path("ventas/", views.sales, name="sales"),
]
