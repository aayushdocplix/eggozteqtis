from datetime import datetime, timedelta

import pytz
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins, permissions
from rest_framework.response import Response

from retailer.api.exportSerializers import RetailerExportSerializer
from retailer.models import Retailer


class RetailerExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = RetailerExportSerializer
    queryset = Retailer.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('salesPersonProfile', 'onboarding_date')

    def list(self, request, *args, **kwargs):

        if request.GET.get('from_onboarding_date') and request.GET.get('to_onboarding_date'):
            from_onboarding_date = datetime.strptime(request.GET.get('from_onboarding_date'), '%d/%m/%Y')
            to_onboarding_date = datetime.strptime(request.GET.get('to_onboarding_date'), '%d/%m/%Y')
            # If date is added automatically
            from_onboarding_date = from_onboarding_date.replace(hour=0, minute=0, second=0)
            to_onboarding_date = to_onboarding_date.replace(hour=0, minute=0, second=0)

            from_onboarding_date = from_onboarding_date
            delta = timedelta(hours=23, minutes=59, seconds=59)
            to_onboarding_date = to_onboarding_date + delta
            print(from_onboarding_date)
            print(to_onboarding_date)
            if request.GET.get('salesPerson'):
                salesPerson = request.GET.get('salesPerson')
                retailers = self.filter_queryset(self.get_queryset().filter(onboarding_date__gte=from_onboarding_date,
                                                                            salesPersonProfile_id=salesPerson,
                                                                            onboarding_date__lte=to_onboarding_date)). \
                    select_related('salesPersonProfile', 'city').order_by('id')
            else:
                retailers = self.filter_queryset(self.get_queryset().filter(onboarding_date__gte=from_onboarding_date,
                                                                            onboarding_date__lte=to_onboarding_date)). \
                    select_related('salesPersonProfile', 'city').order_by('id')
        else:
            if request.GET.get('salesPerson'):
                salesPerson = request.GET.get('salesPerson')
                retailers = self.filter_queryset(self.get_queryset()).filter(salesPersonProfile_id=salesPerson)\
                    .order_by('id')
            else:
                retailers = self.filter_queryset(self.get_queryset()).order_by('id')
        retailer_results = []
        for retailer in retailers:
            retailer_dict = {}
            retailer_dict['RetailerId'] = str(retailer.id)
            retailer_dict['Date Of Onboarding'] = retailer.onboarding_date.strftime(
                '%d/%m/%Y') if retailer.onboarding_date else None
            if retailer.code_int and retailer.code_string:
                retailer_dict['CODE'] = retailer.code_string + str(retailer.code_int) + "* " + retailer.name_of_shop
            else:
                retailer_dict['CODE'] = "Not Added"
            retailer_dict['Short Name'] = retailer.short_name.name if retailer.short_name else 'GT'

            retailer_dict[
                'Sales Person'] = retailer.salesPersonProfile.user.name if retailer.salesPersonProfile else None
            retailer_dict['City'] = retailer.city.city_name
            retailer_dict['CATEGORY'] = retailer.category.name
            retailer_dict['Cluster'] = retailer.cluster.cluster_name
            retailer_dict['Onboarding status'] = retailer.onboarding_status
            retailer_dict['Class'] = retailer.classification.name if retailer.classification else None
            retailer_dict['Name of Shop'] = str(retailer.billing_name_of_shop)
            retailer_dict['SECTOR'] = retailer.sector.sector_name if retailer.sector else None
            retailer_address = retailer.shipping_address
            if retailer_address:
                address = retailer_address.address_name + " - " + retailer_address.building_address
            else:
                address = None
            retailer_dict['Address'] = address
            retailer_dict['Phone No'] = "+" + str(retailer.retailer.phone_no)[-10:]
            retailer_dict['Beat No.'] = str(retailer.beat_number) if int(retailer.beat_number) > 0 else 0
            retailer_dict['Rate Category'] = retailer.commission_slab.number_value if retailer.commission_slab else 0
            retailer_dict['Margin'] = retailer.commission_slab.number if retailer.commission_slab else 0
            retailer_dict['SUB CATEGORY'] = retailer.sub_category.name

            retailer_dict['Pending'] = retailer.amount_due

            retailer_dict['last order date'] = retailer.last_order_date.strftime(
                '%d/%m/%Y') if retailer.last_order_date else None
            retailer_dict['Margin'] = retailer.commission_slab.number if retailer.commission_slab else 0
            retailer_results.append(retailer_dict)
        return Response({"results": retailer_results})

