import uuid
from typing import Optional, List
from ninja import ModelSchema, Schema
from products.models import Category, Product, Review, Favorite

class CategorySchema(ModelSchema):
    class Meta:
        model = Category
        fields = "__all__"


class CategoryCreateSchema(Schema):
    name: str


class ProductSchema(ModelSchema):
    class Meta:
        model = Product
        fields = "__all__"


class ProductCreateSchema(Schema):
    name: str
    description: str
    price: float
    stock: int
    category_id: str


class ProductUpdateSchema(Schema):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock: Optional[int] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None


class ReviewSchema(ModelSchema):
    class Meta:
        model = Review
        fields = "__all__"


class ReviewCreateSchema(Schema):
    product_id: str
    rating: int
    comment: str


class ReviewUpdateSchema(Schema):
    rating: Optional[int] = None
    comment: Optional[str] = None


class FavoriteSchema(ModelSchema):
    class Meta:
        model = Favorite
        fields = "__all__"

class FavoriteCreateSchema(Schema):
    product_id: str


class CategoryWithProductsSchema(Schema):
    id: uuid.UUID
    name: str
    slug: str
    products: List[ProductSchema]

# schema.py (or analytics_schemas.py)

import uuid
from typing import Optional
from ninja import Schema


class CategoryProductCountSchema(Schema):
    category_id: uuid.UUID
    category_name: str
    product_count: int


class ProductRatingAnalyticsSchema(Schema):
    product_id: uuid.UUID
    product_name: str
    average_rating: Optional[float] = None  # May be None if no reviews exist
    review_count: int


class ProductFavoriteAnalyticsSchema(Schema):
    product_id: uuid.UUID
    product_name: str
    favorites_count: int


class OverallAnalyticsSchema(Schema):
    total_categories: int
    total_products: int
    total_reviews: int
    total_favorites: int
