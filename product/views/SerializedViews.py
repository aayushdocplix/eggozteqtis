import json
from ast import literal_eval

from django_filters import rest_framework as filters
from rest_framework import permissions, viewsets, decorators, mixins
from rest_framework.generics import get_object_or_404

from base.api.serializers import UploadDataSerializer
from base.response import BadRequest, Created, Response
from custom_auth.models import UserProfile
from operationschain.models import OperationsPersonProfile
from product.api.serializers import ProductSerializer, ProductDivisionSerializer, BaseProductSerializer, \
    ProductSubDivisionSerializer, EcommerceProductSerializer, ProductShortSerializer
from product.models import Product, ProductDivision, BaseProduct,ProductSubDivision
from product.scripts.upload_product_benefits import upload_product_benefits, upload_product_descriptions
from product.scripts.upload_product_data import upload_product_data


class UploadProductDescriptionsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = upload_product_descriptions(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadProductBenefitsViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = upload_product_benefits(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class UploadProductDataViewSet(viewsets.ViewSet):
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        data = request.data
        serializer = UploadDataSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        csv_file = serializer.validated_data.get('csv_file')
        # let's check if it is a csv file
        csv_file_name = csv_file.name
        if not csv_file_name.endswith('.csv'):
            return BadRequest({"error": "File is not valid"})
        file_response = upload_product_data(csv_file)
        if file_response.get("status") == "success":
            return Created(file_response)
        else:
            return BadRequest(file_response)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'is_available','oms_order', 'ecomm_order', 'brand_type', 'productDivision', 'productSubDivision')

    def list(self, request, *args, **kwargs):
        is_available = request.GET.get('is_available')
        name = request.GET.get('name')
        if is_available:
            # send queried available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available=is_available))
        else:
            # send only available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available=True))
        added_products = request.GET.get('added_products', [])
        if added_products:
            added_products = json.loads(added_products)
            queryset = queryset.exclude(id__in=added_products)
        if name is not None:
            queryset = queryset.filter(name__icontains=name)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="unbranded_list")
    def unbranded_list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductShortViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.CreateModelMixin,
                        mixins.UpdateModelMixin):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProductShortSerializer
    queryset = Product.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'is_available','oms_order', 'ecomm_order', 'brand_type', 'productDivision', 'productSubDivision')



class ProductUpdateViewSet(viewsets.GenericViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = ProductSerializer
    queryset = Product.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'is_available','is_stock_available_online', 'ecomm_order')

    def list(self, request, *args, **kwargs):
        is_available = request.GET.get('is_available')
        if is_available:
            # send queried available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available_online=is_available)).order_by('ecomm_order')
        else:
            # send only available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available=True))
        added_products = request.GET.get('added_products', [])
        if added_products:
            added_products = json.loads(added_products)
            queryset = queryset.exclude(id__in=added_products)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


    @decorators.action(detail=False, methods=['post'], url_path="stock_available")
    def stock_available(self, request, *args, **kwargs):
        data = request.data
        print(data)

        products = request.GET.get('products', [])
        if products and products != "undefined":
            products = json.loads(products)
            products = [int(c) for c in products]
            if len(products) > 0:
                print(products)
                for product in products:
                    product_obj = Product.objects.filter(id=product).first()
                    product_obj.is_stock_available_online = True
                    product_obj.save()
        return Response({})
        # if request.user:
        #     ops_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Operations']).first()
        #     if ops_profile:
        #         opsProfile = OperationsPersonProfile.objects.filter(user=request.user).first()
        #         if opsProfile.management_status == "Worker":
        #             return BadRequest({'error_type': "Not Authorized",
        #                                'errors': [{'message': "please login with Admin Credentials"}]})
        #         else:
        #
        #                products = request.GET.get('products', [])
        #                if products and products != "undefined":
        #                    products = json.loads(products)
        #                 products = [int(c) for c in products]
        #                 if len(products) > 0:
        #                     print(products)
        #                     for product in products:
        #                         product_obj = Product.objects.filter(id=product).first()
        #                         product_obj.is_stock_available_online=True
        #                         product_obj.save()
        #                 else:
        #                     return BadRequest({'error_type': "Validation Error",
        #                                        'errors': [{'message': "please provide at least one product to assign"}]})
        #     else:
        #         return BadRequest({'error_type': "Not Authorized",
        #                            'errors': [{'message': "please login with Admin Credentials"}]})


    @decorators.action(detail=False, methods=['post'], url_path="out_of_stock")
    def out_of_stock(self, request, *args, **kwargs):
        data = request.data
        print(data)
        products = request.GET.get('products', [])
        if products and products != "undefined":
            products = json.loads(products)
            products = [int(c) for c in products]
            if len(products) > 0:
                print(products)
                for product in products:
                    product_obj = Product.objects.filter(id=product).first()
                    product_obj.is_stock_available_online = False
                    product_obj.save()
        return Response({})
        # if request.user:
        #     ops_profile = UserProfile.objects.filter(user=request.user, department__name__in=['Operations']).first()
        #     if ops_profile:
        #         opsProfile = OperationsPersonProfile.objects.filter(user=request.user).first()
        #         if opsProfile.management_status == "Worker":
        #             return BadRequest({'error_type': "Not Authorized",
        #                                'errors': [{'message': "please login with Admin Credentials"}]})
        #         else:
        #             products = request.GET.get('products', [])
        #             if products and products != "undefined":
        #                 products = json.loads(products)
        #                 products = [int(c) for c in products]
        #                 if len(products) > 0:
        #                     print(products)
        #                     for product in products:
        #                         product_obj = Product.objects.filter(id=product).first()
        #                         product_obj.is_stock_available_online = False
        #                         product_obj.save()
        #                 else:
        #                     return BadRequest({'error_type': "Validation Error",
        #                                        'errors': [{'message': "please provide at least one product to assign"}]})
        #     else:
        #         return BadRequest({'error_type': "Not Authorized",
        #                            'errors': [{'message': "please login with Admin Credentials"}]})


class EcommerceProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.AllowAny,)
    serializer_class = EcommerceProductSerializer
    queryset = Product.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'is_available','is_available_online','ecomm_order', 'brand_type', 'productDivision')

    def list(self, request, *args, **kwargs):
        is_available = request.GET.get('is_available')
        if is_available:
            # send queried available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available_online=is_available)).order_by('ecomm_order')
        else:
            # send only available products
            queryset = self.filter_queryset(self.get_queryset().filter(is_available=True))
        added_products = request.GET.get('added_products', [])
        if added_products:
            added_products = json.loads(added_products)
            queryset = queryset.exclude(id__in=added_products)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class BaseProductViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = BaseProductSerializer
    queryset = BaseProduct.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('city', 'productDivision')

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        added_products = request.GET.get('added_products', [])
        if added_products:
            added_products = json.loads(added_products)
            queryset = queryset.exclude(id__in=added_products)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class ProductDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProductDivisionSerializer
    queryset = ProductDivision.objects.filter(is_visible=True)


class ProductSubDivisionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = ProductSubDivisionSerializer
    queryset = ProductSubDivision.objects.filter(is_visible=True)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('productDivision',)
