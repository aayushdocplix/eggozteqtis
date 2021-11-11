from datetime import datetime

import pytz
from django.db import models
from django.db.models import Max
from uuid_upload_path import upload_to

from Eggoz import settings
from distributionchain.models import DistributionPersonProfile, BeatAssignment
from ecommerce.models import Customer
from finance.models import FinanceProfile
from order.models import Order
from retailer.models import Retailer
from saleschain.models import SalesPersonProfile


class Invoice(models.Model):
    invoice_id = models.CharField(max_length=254)
    order = models.OneToOneField(
        Order, related_name="invoice", on_delete=models.DO_NOTHING, null=True, blank=True
    )
    file = models.FileField(upload_to=upload_to, null=True, blank=True)
    invoice_due = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    STATUS_CHOICES = (('Pending', 'Pending'), ('Paid', 'Paid'),('Cancelled', 'Cancelled'),
                      ('Adjusted','Adjusted'), ('Waiveoff','Waiveoff'),
                      ('Bad debt', 'Bad debt'))
    invoice_status = models.CharField(choices=STATUS_CHOICES, default='Pending', max_length=100)
    created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.invoice_id

    class Meta:
        ordering = ('id', )


class InvoiceLine(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.DO_NOTHING,
                                related_name="invoice_lines")
    amount_received = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    received_at = models.DateTimeField(auto_now_add=True)
    sales_transaction = models.ForeignKey('payment.SalesTransaction', on_delete=models.CASCADE, null=True, blank=True)


class SalesTransaction(models.Model):
    retailer = models.ForeignKey(Retailer, on_delete=models.DO_NOTHING, null=True, blank=True,
                                 related_name="transaction")

    customer = models.ForeignKey(Customer, on_delete=models.DO_NOTHING, null=True, blank=True,
                                 related_name="customer_transaction")
    beat_assignment = models.ForeignKey(BeatAssignment, null=True, blank=True, on_delete=models.DO_NOTHING)
    TYPE_CHOICES = (('Credit', 'Credit'),
                    ('Debit', 'Debit'),
                    ('Refund', 'Refund'),
                    ('Return', 'Return'),
                    ('Promo', 'Promo'),
                    ('Replacement', 'Replacement'),
                    ('Debit Note', 'Debit Note'),
                    ('Adjusted','Adjusted'),
                    ('Cancelled', 'Cancelled'))
    transaction_id = models.CharField(max_length=254, null=True)
    transaction_type = models.CharField(choices=TYPE_CHOICES, max_length=200)
    salesPerson = models.ForeignKey(SalesPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="transaction")
    financePerson = models.ForeignKey(FinanceProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="finance_transaction")
    distributor = models.ForeignKey(DistributionPersonProfile, on_delete=models.DO_NOTHING, null=True, blank=True,
                                    related_name="distributor_transaction")
    transaction_date = models.DateTimeField(null=True, blank=True)
    transaction_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    invoices = models.ManyToManyField(Invoice, related_name='sales_invoices', blank=True)
    remarks = models.CharField(max_length=254, null=True)
    current_balance = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    is_verified = models.BooleanField(default=False)
    is_trial = models.BooleanField(default=False)

    def __str__(self):
        if self.retailer:
            return "{}- {}".format(str(self.id), self.retailer.id)
        else:
            return "{}- {}"

    def sales_transaction_date(self):
        return self.transaction_date

    class Meta:
        ordering = ['transaction_date','id',]


class Payment(models.Model):
    TYPE_CHOICES = (('Cash', 'Cash'),
                    ('Cheque', 'Cheque'),
                    ('UPI', 'UPI'))
    PAY_CHOICES = (('InstantPay', 'InstantPay'),
                   ('LaterPay', 'LaterPay'), ('Refund', 'Refund'),
                   ('Replacement', 'Replacement'),
                   ('Return', 'Return'))
    payment_type = models.CharField(choices=TYPE_CHOICES, max_length=200)
    payment_mode = models.CharField(max_length=200, default='PETTY CASH')
    pay_choice = models.CharField(choices=PAY_CHOICES, max_length=200, default="InstantPay")

    cheque_number = models.CharField(max_length=200, null=True, blank=True)
    upi_id = models.CharField(max_length=200, null=True, blank=True)
    pay_amount = models.DecimalField(
        max_digits=settings.DEFAULT_MAX_DIGITS,
        decimal_places=settings.DEFAULT_DECIMAL_PLACES,
        default=0,
    )
    invoice = models.ForeignKey(Invoice, related_name='payment_invoice', blank=True, null=True, on_delete=models.CASCADE)
    salesTransaction = models.ForeignKey(SalesTransaction, on_delete=models.DO_NOTHING,
                                         related_name="paymentTransactions")
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ('salesTransaction__transaction_date',)

    def payment_date(self):
        if self.created_at:
            return self.created_at
        elif self.salesTransaction.transaction_date:
            return self.salesTransaction.transaction_date
        else:
            return "No Date"
