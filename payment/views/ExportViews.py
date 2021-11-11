from datetime import datetime, timedelta

import pytz
from rest_framework import viewsets, mixins, permissions

from django_filters import rest_framework as filters

from payment.api.exportSerializers import SalesTransactionExportSerializer
from payment.models import SalesTransaction, Payment

from rest_framework.response import Response


class SalesTransactionsExportViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = SalesTransactionExportSerializer
    queryset = SalesTransaction.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('transaction_type', 'transaction_date', 'salesPerson', 'retailer')

    def list(self, request, *args, **kwargs):

        if request.GET.get('from_transaction_date') and request.GET.get('to_transaction_date'):
            from_transaction_date = datetime.strptime(request.GET.get('from_transaction_date'), '%d/%m/%Y')
            to_transaction_date = datetime.strptime(request.GET.get('to_transaction_date'), '%d/%m/%Y')

            from_transaction_date = from_transaction_date.replace(hour=0, minute=0, second=0)
            to_transaction_date = to_transaction_date.replace(hour=0, minute=0, second=0)

            delta = timedelta(hours=23, minutes=59, seconds=59)
            from_transaction_date = from_transaction_date
            to_transaction_date = to_transaction_date + delta

            transactions = self.filter_queryset(self.get_queryset().filter(transaction_date__gte=from_transaction_date,
                                                                           transaction_date__lte=to_transaction_date,is_trial=False)). \
                select_related('salesPerson','distributor', 'retailer').order_by('transaction_date')
        else:
            transactions = self.filter_queryset(self.get_queryset().filter(is_trial=False))
        transaction_results = []
        for transaction in transactions:
            transaction_dict = {}
            transaction_dict['Transaction Date'] = transaction.transaction_date
            transaction_dict['retailer'] = transaction.retailer.name_of_shop if transaction.retailer else None
            invoices = transaction.invoices.all()
            transaction_dict['Bill No'] = "&".join([str(i.order.name) for i in invoices]) if invoices else None
            payments = transaction.paymentTransactions.all()
            transaction_dict['Transaction Type'] = transaction.transaction_type
            transaction_dict['Transaction Id'] = transaction.transaction_id
            if transaction.transaction_type == "Debit":
                transaction_dict['Debit'] = str(int(transaction.transaction_amount))
                transaction_dict['Credit'] = ''
                transaction_dict['Return Or Replacements'] = ''
                transaction_dict["pay mode"] = ""
            elif transaction.transaction_type == "Credit":
                transaction_dict['Debit'] = ''
                transaction_dict['Credit'] = str(int(transaction.transaction_amount))
                transaction_dict['Return Or Replacements'] = ''
                transaction_dict["pay mode"] = "&".join(["{}".format(p.payment_mode) for
                                                         p in payments])
            else:
                transaction_dict['Debit'] = ''
                transaction_dict['Credit'] = ''
                transaction_dict['Return Or Replacements'] = str(int(transaction.transaction_amount))
                transaction_dict["pay mode"] = "&".join(["{}".format(p.payment_mode) for
                                                         p in payments])


            transaction_results.append(transaction_dict)
        return Response({"results": transaction_results})
