# api.py

import uuid
from ninja import NinjaAPI, File
from typing import List, Optional
from ninja.files import UploadedFile
from users.models import ArtistProfile, User
from django.shortcuts import get_object_or_404
from utils.base import get_authenticated_user, parse_uuid
from products.models import Category, Product, Review, Favorite
from .schema import (
    CategorySchema,
    CategoryCreateSchema,
    ProductSchema,
    ProductUpdateSchema,
    ProductCreateSchema,
    ReviewSchema,
    ReviewCreateSchema,
    FavoriteSchema,
    FavoriteCreateSchema,
    CategoryWithProductsSchema,
)

api = NinjaAPI()


@api.get("/products", response=List[ProductSchema])
def list_products(request):
    return list(Product.objects.all())


@api.get("/products-by-category", response=List[CategoryWithProductsSchema])
def products_by_category(request):
    categories = Category.objects.all().prefetch_related("products")

    result = []

    for category in categories:
        result.append(
            {
                "id": category.id,
                "name": category.name,
                "slug": category.slug,
                "products": [
                    ProductSchema.from_orm(prod) for prod in category.products.all()  # type: ignore
                ],
            }
        )
    return result


@api.get("/products/{product_id}", response=ProductSchema)
def get_product(request, product_id: str):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    return Product.objects.get(artist=artist, id=parse_uuid(product_id))


@api.post("/products", response=dict)
def create_product(
    request,
    data: ProductCreateSchema,
    file: UploadedFile = File(...),  # type: ignore
):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.create(
        artist=artist,
        name=data.name,
        description=data.description,
        price=data.price,
        stock=data.stock,
    )

    category = Category.objects.get(id=parse_uuid(data.category_id))

    product.category = category

    product.save()

    product.image.save(file.name, file, save=True)

    return {"message": "Product created successfully"}


@api.put("/products/{product_id}", response=dict)
def update_product(
    request,
    product_id: str,
    data: ProductUpdateSchema,
    file: Optional[UploadedFile] = File(...),  # type: ignore
):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(product_id))

    if data.name is not None:
        product.name = data.name

    if data.description is not None:
        product.description = data.description

    if data.price is not None:
        product.price = float(data.price)  # type: ignore

    if data.stock is not None:
        product.stock = data.stock

    if data.is_active is not None:
        product.is_active = data.is_active

    if data.category_id is not None:
        category = Category.objects.get(id=parse_uuid(data.category_id))

        product.category = category

    if file:
        product.image.save(file.name, file, save=True)

    product.save()

    return {"message": "Product updated successfully"}


@api.delete("/products/{product_id}", response=dict)
def delete_product(request, product_id: str):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(product_id))

    product.delete()

    return {"message": "Product deleted successfully"}


@api.get("/reviews", response=List[ReviewSchema])
def list_reviews(request):
    return list(Review.objects.all())


@api.get("/reviews/{review_id}", response=ReviewSchema)
def get_review(request, review_id: str):
    user = get_authenticated_user(request)

    return Review.objects.get(user=user, id=parse_uuid(review_id))


@api.post("/reviews", response=dict)
def create_review(request, data: ReviewCreateSchema):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(data.product_id))

    Review.objects.create(
        product=product,
        user=user,
        rating=data.rating,
        comment=data.comment,
    )

    return {"message": "Review created successfully"}


@api.put("/reviews/{review_id}", response=dict)
def update_review(request, review_id: str, data: ReviewCreateSchema):
    user = get_authenticated_user(request)

    review = Review.objects.get(user=user, id=parse_uuid(review_id))

    if data.rating:
        review.rating = data.rating

    if data.comment:
        review.comment = data.comment

    review.save()

    return {"message": "Review updated successfully"}


@api.delete("/reviews/{review_id}", response=dict)
def delete_review(request, review_id: str):
    user = get_authenticated_user(request)

    review = Review.objects.get(user=user, id=parse_uuid(review_id))

    review.delete()

    return {"message": "Review deleted successfully"}


@api.get("/favorites", response=List[FavoriteSchema])
def list_favorites(request):
    return list(Favorite.objects.all())


# @api.get("/favorites/{favorite_id}", response=FavoriteSchema)
# def get_favorite(request, favorite_id: str):
#     favorite = get_object_or_404(Favorite, id=favorite_id)
#     return favorite


@api.post("/favorites", response=dict)
def create_favorite(request, data: FavoriteCreateSchema):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(data.product_id))

    Favorite.objects.create(
        user=user,
        product=product,
    )

    return {"message": "Favorite created"}


@api.delete("/favorites", response=dict)
def delete_favorite(request, data: FavoriteCreateSchema):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(data.product_id))

    Favorite.objects.get(
        user=user,
        product=product,
    ).delete()

    return {"message": "Favorite removed"}
