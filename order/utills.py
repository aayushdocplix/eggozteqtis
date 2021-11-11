from payment.models import Invoice
from decimal import Decimal
def make_invoice_clear():
    Invoice.objects.filter(invoice_status="Pending",invoice_due=Decimal(0)).update(invoice_status="Paid")