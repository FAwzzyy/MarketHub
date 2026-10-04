from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from django.core.cache import cache

from .models import Product
from .permissions import IsStaffOrReadOnly
from .serializers import ProductSerializer


PRODUCT_LIST_CACHE_KEY = "products:list"
PRODUCT_DETAIL_CACHE_KEY = "products:detail:{}"
CACHE_TIMEOUT = 300


def invalidate_product_cache(product_id=None):
    cache.delete(PRODUCT_LIST_CACHE_KEY)

    if product_id is not None:
        cache.delete(
            PRODUCT_DETAIL_CACHE_KEY.format(product_id)
        )


@api_view(["GET", "POST"])
@permission_classes([IsStaffOrReadOnly])
def product_list(request):

    if request.method == "GET":

        cached_products = cache.get(
            PRODUCT_LIST_CACHE_KEY
        )

        if cached_products is not None:
            return Response(cached_products)

        products = Product.objects.select_related("category")

        serializer = ProductSerializer(
            products,
            many=True
        )

        cache.set(
            PRODUCT_LIST_CACHE_KEY,
            serializer.data,
            CACHE_TIMEOUT
        )

        return Response(serializer.data)

    elif request.method == "POST":
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            product = serializer.save()

            invalidate_product_cache(product.id)

            return Response(
                ProductSerializer(product).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsStaffOrReadOnly])
def product_detail(request, pk):

    cache_key = PRODUCT_DETAIL_CACHE_KEY.format(pk)

    if request.method == "GET":

        cached_product = cache.get(cache_key)

        if cached_product is not None:
            return Response(cached_product)

        try:
            product = Product.objects.select_related(
                "category"
            ).get(pk=pk)

        except Product.DoesNotExist:
            return Response(
                {"detail": "Product not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ProductSerializer(product)

        cache.set(
            cache_key,
            serializer.data,
            CACHE_TIMEOUT
        )

        return Response(serializer.data)

    try:
        product = Product.objects.get(pk=pk)

    except Product.DoesNotExist:
        return Response(
            {"detail": "Product not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "PUT":
        serializer = ProductSerializer(
            product,
            data=request.data
        )

        if serializer.is_valid():
            product = serializer.save()

            invalidate_product_cache(product.id)

            return Response(
                ProductSerializer(product).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == "PATCH":
        serializer = ProductSerializer(
            product,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            product = serializer.save()

            invalidate_product_cache(product.id)

            return Response(
                ProductSerializer(product).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == "DELETE":
        product_id = product.id

        product.delete()

        invalidate_product_cache(product_id)

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )