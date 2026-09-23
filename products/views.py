from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response

from .models import Product
from .permissions import IsStaffOrReadOnly
from .serializers import ProductSerializer


@api_view(["GET", "POST"])
@permission_classes([IsStaffOrReadOnly])
def product_list(request):

    if request.method == "GET":
        products = Product.objects.all()
        serializer = ProductSerializer(products, many=True)

        return Response(serializer.data)

    elif request.method == "POST":
        serializer = ProductSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()

            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@permission_classes([IsStaffOrReadOnly])
def product_detail(request, pk):

    try:
        product = Product.objects.get(pk=pk)

    except Product.DoesNotExist:
        return Response(
            {"detail": "Product not found."},
            status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        serializer = ProductSerializer(product)

        return Response(serializer.data)

    elif request.method == "PUT":
        serializer = ProductSerializer(
            product,
            data=request.data
        )

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)

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
            serializer.save()

            return Response(serializer.data)

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    elif request.method == "DELETE":
        product.delete()

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )