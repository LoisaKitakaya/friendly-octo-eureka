# router.py

from typing import List
from ninja import Router, File
from typing import List, Optional
from ninja.files import UploadedFile
from users.models import ArtistProfile
from django.db.models import Count, Avg
from products.models import Category, Product, Review, Favorite
from utils.base import (
    parse_uuid,
    AuthBearer,
    require_role,
    require_active,
    get_authenticated_user,
)
from .schema import (
    CategoryProductCountSchema,
    ProductRatingAnalyticsSchema,
    ProductFavoriteAnalyticsSchema,
    OverallAnalyticsSchema,
    ProductSchema,
    ProductUpdateSchema,
    ProductCreateSchema,
    ReviewSchema,
    ReviewCreateSchema,
    FavoriteSchema,
    FavoriteCreateSchema,
    CategoryWithProductsSchema,
    CategorySchema,
)

router = Router()

bearer = AuthBearer()


@router.get("/categories", response=List[CategorySchema])
def list_categories(request):
    return list(Category.objects.all())


@router.get("/products", auth=bearer, response=List[ProductSchema])
@require_active
def list_products(request):
    return list(Product.objects.all())


@router.get(
    "/products-by-category", auth=bearer, response=List[CategoryWithProductsSchema]
)
@require_active
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


@router.get("/products/{product_id}", auth=bearer, response=ProductSchema)
@require_active
@require_role(is_artist=True)
def get_product(request, product_id: str):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    return Product.objects.get(artist=artist, id=parse_uuid(product_id))


@router.post("/products", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
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


@router.put("/products/{product_id}", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
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


@router.delete("/products/{product_id}", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def delete_product(request, product_id: str):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(product_id))

    product.delete()

    return {"message": "Product deleted successfully"}


@router.get("/reviews", auth=bearer, response=List[ReviewSchema])
@require_active
def list_reviews(request):
    return list(Review.objects.all())


@router.get("/reviews/{review_id}", auth=bearer, response=ReviewSchema)
@require_active
def get_review(request, review_id: str):
    user = get_authenticated_user(request)

    return Review.objects.get(user=user, id=parse_uuid(review_id))


@router.post("/reviews", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
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


@router.put("/reviews/{review_id}", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def update_review(request, review_id: str, data: ReviewCreateSchema):
    user = get_authenticated_user(request)

    review = Review.objects.get(user=user, id=parse_uuid(review_id))

    if data.rating:
        review.rating = data.rating

    if data.comment:
        review.comment = data.comment

    review.save()

    return {"message": "Review updated successfully"}


@router.delete("/reviews/{review_id}", auth=bearer, response=dict)
@require_active
@require_role(is_artist=True)
def delete_review(request, review_id: str):
    user = get_authenticated_user(request)

    review = Review.objects.get(user=user, id=parse_uuid(review_id))

    review.delete()

    return {"message": "Review deleted successfully"}


@router.get("/favorites", auth=bearer, response=List[FavoriteSchema])
@require_active
def list_favorites(request):
    return list(Favorite.objects.all())


# @router.get("/favorites/{favorite_id}", response=FavoriteSchema)
# def get_favorite(request, favorite_id: str):
#     favorite = get_object_or_404(Favorite, id=favorite_id)
#     return favorite


@router.post("/favorites", auth=bearer, response=dict)
@require_active
def create_favorite(request, data: FavoriteCreateSchema):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(data.product_id))

    Favorite.objects.create(
        user=user,
        product=product,
    )

    return {"message": "Favorite created"}


@router.delete("/favorites", auth=bearer, response=dict)
@require_active
def delete_favorite(request, data: FavoriteCreateSchema):
    user = get_authenticated_user(request)

    artist = ArtistProfile.objects.get(user=user)

    product = Product.objects.get(artist=artist, id=parse_uuid(data.product_id))

    Favorite.objects.get(
        user=user,
        product=product,
    ).delete()

    return {"message": "Favorite removed"}


@router.get(
    "/analytics/products-count-per-category",
    auth=bearer,
    response=List[CategoryProductCountSchema],
)
@require_active
@require_role(is_artist=True)
def products_count_per_category(request):
    categories = Category.objects.annotate(product_count=Count("products"))
    result = []
    for cat in categories:
        result.append(
            {
                "category_id": cat.id,
                "category_name": cat.name,
                "product_count": cat.product_count,  # type: ignore
            }
        )
    return result


@router.get(
    "/analytics/product-ratings",
    auth=bearer,
    response=List[ProductRatingAnalyticsSchema],
)
@require_active
@require_role(is_artist=True)
def product_ratings_analytics(request):
    products = Product.objects.annotate(
        average_rating=Avg("reviews__rating"), review_count=Count("reviews")
    )
    result = []
    for prod in products:
        result.append(
            {
                "product_id": prod.id,
                "product_name": prod.name,
                "average_rating": prod.average_rating,  # type: ignore
                "review_count": prod.review_count,  # type: ignore
            }
        )
    return result


@router.get(
    "/analytics/product-favorites",
    auth=bearer,
    response=List[ProductFavoriteAnalyticsSchema],
)
@require_active
@require_role(is_artist=True)
def product_favorites_analytics(request):
    products = Product.objects.annotate(favorites_count=Count("favorited_by"))
    result = []
    for prod in products:
        result.append(
            {
                "product_id": prod.id,
                "product_name": prod.name,
                "favorites_count": prod.favorites_count,  # type: ignore
            }
        )
    return result


@router.get("/analytics/summary", auth=bearer, response=OverallAnalyticsSchema)
@require_active
@require_role(is_artist=True)
def overall_analytics(request):
    total_categories = Category.objects.count()
    total_products = Product.objects.count()
    total_reviews = Review.objects.count()
    total_favorites = Favorite.objects.count()

    return {
        "total_categories": total_categories,
        "total_products": total_products,
        "total_reviews": total_reviews,
        "total_favorites": total_favorites,
    }
