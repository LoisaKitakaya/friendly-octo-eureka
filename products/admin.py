from django.contrib import admin
from .models import Category, Product, Review, Favorite


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "artist",
        "price",
        "stock",
        "category",
        "is_active",
        "created_at",
    )
    list_filter = ("is_active", "category", "artist")
    search_fields = ("name", "artist__store_name")
    prepopulated_fields = {"slug": ("name",)}
    list_editable = ("price", "stock", "is_active")
    date_hierarchy = "created_at"


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "user", "rating", "created_at")
    list_filter = ("rating", "created_at")
    search_fields = ("product__name", "user__username")


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ("user", "product", "created_at")
    search_fields = ("user__username", "product__name")
