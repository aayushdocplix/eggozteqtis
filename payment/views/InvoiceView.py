import decimal

from django.db.models import Max
from django_filters import rest_framework as filters
from rest_framework import viewsets, permissions
from order.tasks import create_invoice

from base.views import PaginationWithNoLimit
from order.models import Order
from payment.api.serializers import InvoiceShortSerializer
from payment.models import Invoice


class InvoiceViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = InvoiceShortSerializer
    pagination_class = PaginationWithNoLimit
    queryset = Invoice.objects.all()
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ('invoice_status', 'order__retailer', 'order__salesPerson')


def generate_invoice(data, returned_amount):
    request = data.get('request')
    order_ids = data.get('order_ids')
    for order_id in order_ids:
        order = Order.objects.filter(id=order_id).first()
        if order:
            invoice = Invoice.objects.filter(order=order).first()
            if not invoice:
                invoices = Invoice.objects.all()
                # might be possible model has no records so make sure to handle None
                invoice_max_id = invoices.aggregate(Max('id'))['id__max'] + 1 if invoices else 1
                invoice_id = "E" + str(invoice_max_id)
                # invoice_due = order.order_price_amount + order.retailer.amount_due
                invoice_due = order.order_price_amount - decimal.Decimal(returned_amount)
                # created_at = CURRENT_ZONE.localize(order.delivery_date)
                #TODO Validte for negative due
                print(order.delivery_date)
                invoice = Invoice.objects.create(order=order, invoice_id=invoice_id, created_at=order.delivery_date,
                                                 invoice_due=invoice_due)
                if invoice_due <= 0:
                    invoice.invoice_status = "Paid"
                    invoice.save()
            invoice.file = None
            invoice.save()
            # create_invoice.delay(order.id, request.build_absolute_uri())
        else:
            continue
