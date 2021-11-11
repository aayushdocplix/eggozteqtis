from rest_framework import pagination, viewsets, mixins, permissions, decorators

from base.response import BadRequest, NotFound
from base.views import PaginationWithNoLimit
from custom_auth.models import UserProfile
from finance.api.serializers import FinanceProfileSerializer, FinancePersonHistorySerializer
from finance.models import FinanceProfile

from rest_framework.response import Response

from retailer.api.serializers import RetailerMarginSerializer, RetailerFinanceSerializer
from retailer.models import Retailer


class PaginationWithLimit(pagination.PageNumberPagination):
    page_size = 1000


class FinanceProfileViewSet(viewsets.GenericViewSet, mixins.ListModelMixin, mixins.RetrieveModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    pagination_class = PaginationWithNoLimit
    serializer_class = FinanceProfileSerializer
    queryset = FinanceProfile.objects.all()

    def list(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Finance']).first()
        if user_profile:
            financeProfile = FinanceProfile.objects.filter(user=user).first()
            if financeProfile.management_status == "Worker":
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "please login with Admin Credentials"}]})
            else:
                queryset = FinanceProfile.objects.filter().exclude(
                    user=user).distinct()
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No User Profile"}]})
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @decorators.action(detail=False, methods=['get'], url_path="retailers")
    def retailers(self, request, *args, **kwargs):
        user = request.user
        user_profile = UserProfile.objects.filter(user=user, department__name__in=['Finance']).first()
        # queryset = None
        if user_profile:
            financeProfile = FinanceProfile.objects.filter(user=user).first()
            if financeProfile:
                queryset = Retailer.objects.all()
            else:
                return BadRequest({'error_type': "Not Authorized",
                                   'errors': [{'message': "No Finance Profile"}]})
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = RetailerFinanceSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = RetailerFinanceSerializer(queryset, many=True)

            return Response(serializer.data)
        else:
            return BadRequest({'error_type': "Not Authorized",
                               'errors': [{'message': "No Finance User Profile"}]})

